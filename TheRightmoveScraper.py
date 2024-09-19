class TheRightmoveScraper:
    """The `RightmoveData` web scraper collects structured data on properties
    returned by a search performed on www.rightmove.co.uk.

    An instance of the class provides attributes to access data from the search
    results, the most useful being `get_results`, which returns all results as a
    Pandas DataFrame object.

    The query to Rightmove can be renewed by calling the `refresh_data` method.
    """

    
    POSTCODE_PATTERN = re.compile(r"\b([A-Za-z]{1,2}\d{1,2}[A-Za-z]?)\b")
    FULL_POSTCODE_PATTERN = re.compile(
        r"([A-Za-z]{1,2}\d{1,2}[A-Za-z]?\s\d{1}[A-Za-z]{2})"
    )
    BEDROOM_PATTERN = re.compile(r"\b(\d+)\b")
    PRICE_CLEAN_PATTERN = re.compile(r"[^\d]")
    MAX_WORKERS = 10  

    def __init__(self, url: str, get_floorplans: bool = False):
        """Initialize the scraper with a URL from the results of a property
        search performed on www.rightmove.co.uk.

        Args:
            url (str): The full URL to a Rightmove search result page.
            get_floorplans (bool): Optionally scrape links to floor plan images
                for each listing (increases runtime). False by default.
        """
        self._url = url
        self._get_floorplans = get_floorplans
        self._status_code, self._first_page = self._request(url)
        self._validate_url()
        self._results = self._get_results(get_floorplans=get_floorplans)

    @staticmethod
    def _request(url: str) -> (Optional[int], Optional[bytes]):
        """Make an HTTP GET request to the specified URL."""
        headers = {
            'User-Agent': (
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/70.0.3538.77 Safari/537.36'
            )
        }
        try:
            response = requests.get(url, timeout=10, headers=headers)
            response.raise_for_status()
            return response.status_code, response.content
        except requests.RequestException as e:
            logger.error(f"Request failed for URL: {url}\nError: {e}")
            return None, None

    def refresh_data(self, url: Optional[str] = None, get_floorplans: bool = False):
        """Refresh the data by making a new GET request.

        Args:
            url (str): Optionally pass a new URL to Rightmove search results.
            get_floorplans (bool): Optionally scrape links to floor plan images
                (increases runtime). False by default.
        """
        self._url = url or self.url
        self._get_floorplans = get_floorplans
        self._status_code, self._first_page = self._request(self.url)
        self._validate_url()
        self._results = self._get_results(get_floorplans=get_floorplans)

    def _validate_url(self):
        """Validate that the URL is a valid Rightmove search URL."""
        if self._status_code != 200:
            raise ValueError(
                f"Invalid Rightmove URL (status code {self._status_code}):\n\n\t{self.url}"
            )
        url_patterns = [
            r"https?://www\.rightmove\.co\.uk/property-for-sale/find\.html\?",
            r"https?://www\.rightmove\.co\.uk/property-to-rent/find\.html\?",
            r"https?://www\.rightmove\.co\.uk/new-homes-for-sale/find\.html\?",
            r"https?://www\.rightmove\.co\.uk/commercial-property-for-sale/find\.html\?",
            r"https?://www\.rightmove\.co\.uk/commercial-property-to-let/find\.html\?",
        ]
        if not any(re.match(pattern, self.url) for pattern in url_patterns):
            raise ValueError(f"Invalid Rightmove search URL:\n\n\t{self.url}")

    @property
    def url(self) -> str:
        return self._url

    @property
    def get_results(self) -> pd.DataFrame:
        """Pandas DataFrame of all results returned by the search."""
        return self._results

    @property
    def results_count(self) -> int:
        """Total number of results returned by `get_results`."""
        return len(self.get_results)

    @property
    def average_price(self) -> float:
        """Average price of all results returned by `get_results`."""
        total = self.get_results["price"].dropna().sum()
        if self.results_count == 0:
            return 0.0
        return total / self.results_count

    def summary(self, by: str = None) -> pd.DataFrame:
        """DataFrame summarizing results by mean price and count.

        Args:
            by (str): Valid column name from `get_results` DataFrame attribute.
                Defaults to 'number_bedrooms' or 'type' based on property type.
        """
        if not by:
            by = "type" if "commercial" in self.rent_or_sale else "number_bedrooms"
        if by not in self.get_results.columns:
            raise ValueError(f"Column not found in `get_results`: {by}")

        df = self.get_results.dropna(subset=["price"])
        summary_df = df.groupby(by).agg({'price': ['count', 'mean']})
        summary_df.columns = summary_df.columns.get_level_values(1)
        summary_df.reset_index(inplace=True)

        if by == "number_bedrooms":
            summary_df["number_bedrooms"] = summary_df["number_bedrooms"].astype(int)
            summary_df.sort_values(by="number_bedrooms", inplace=True)
        else:
            summary_df.sort_values(by="count", ascending=False, inplace=True)

        return summary_df.reset_index(drop=True)

    @property
    def rent_or_sale(self) -> str:
        """Determine if the search is for properties for rent or sale."""
        url = self.url
        if "/property-for-sale/" in url or "/new-homes-for-sale/" in url:
            return "sale"
        elif "/property-to-rent/" in url:
            return "rent"
        elif "/commercial-property-for-sale/" in url:
            return "sale-commercial"
        elif "/commercial-property-to-let/" in url:
            return "rent-commercial"
        else:
            raise ValueError(f"Invalid Rightmove URL:\n\n\t{self.url}")

    @property
    def results_count_display(self) -> int:
        """Total number of listings as displayed on the first page of results."""
        tree = html.fromstring(self._first_page)
        xpath = "//span[@class='searchHeader-resultCount']/text()"
        result = tree.xpath(xpath)
        if result:
            return int(result[0].replace(",", ""))
        else:
            return 0

    @property
    def page_count(self) -> int:
        """Number of result pages returned by the search URL."""
        count = self.results_count_display
        page_count = count // 24
        if count % 24 > 0:
            page_count += 1
        return min(page_count, 42) 

    def _get_page(self, request_content: bytes, get_floorplans: bool = False) -> pd.DataFrame:
        """Scrape data from a single page of search results."""
        if not request_content:
            return pd.DataFrame()

        tree = html.fromstring(request_content)
        base = "https://www.rightmove.co.uk"

        if "rent" in self.rent_or_sale:
            xp_prices = '//span[@class="propertyCard-priceValue"]/text()'
        else:
            xp_prices = '//div[@class="propertyCard-priceValue"]/text()'

        xp_titles = (
            '//div[@class="propertyCard-details"]//a[@class="propertyCard-link"]'
            '//h2[@class="propertyCard-title"]/text()'
        )
        xp_addresses = '//address[@class="propertyCard-address"]//span/text()'
        xp_weblinks = '//div[@class="propertyCard-details"]//a[@class="propertyCard-link"]/@href'
        xp_agent_urls = (
            '//div[@class="propertyCard-contact"]//a[@class="propertyCard-branchLogo-link"]/@href'
        )

        # Extract data using XPaths
        prices = tree.xpath(xp_prices)
        titles = tree.xpath(xp_titles)
        addresses = tree.xpath(xp_addresses)
        weblinks = [f"{base}{link}" for link in tree.xpath(xp_weblinks)]
        agent_urls = [f"{base}{link}" for link in tree.xpath(xp_agent_urls)]

        if get_floorplans:
            floorplan_urls = self._fetch_floorplans(weblinks)
        else:
            floorplan_urls = [np.nan] * len(weblinks)

        max_length = max(len(prices), len(titles), len(addresses), len(weblinks), len(agent_urls))
        data = {
            "price": prices + [np.nan] * (max_length - len(prices)),
            "type": titles + [np.nan] * (max_length - len(titles)),
            "address": addresses + [np.nan] * (max_length - len(addresses)),
            "url": weblinks + [np.nan] * (max_length - len(weblinks)),
            "agent_url": agent_urls + [np.nan] * (max_length - len(agent_urls)),
            "floorplan_url": floorplan_urls + [np.nan] * (max_length - len(floorplan_urls)),
        }
        df = pd.DataFrame(data)
        df.dropna(subset=["address"], inplace=True) 
        return df

    def _fetch_floorplans(self, weblinks: List[str]) -> List[Optional[str]]:
        """Fetch floorplan URLs using multiple threads for efficiency."""
        with ThreadPoolExecutor(max_workers=self.MAX_WORKERS) as executor:
            results = list(executor.map(self._get_floorplan_url, weblinks))
        return results

    def _get_floorplan_url(self, weblink: str) -> Optional[str]:
        """Fetch floorplan URL for a single property listing."""
        try:
            status_code, content = self._request(weblink)
            if status_code != 200 or not content:
                return np.nan
            tree = html.fromstring(content)
            xp_floorplan_url = '//*[@id="floorplanTabs"]//img/@src'
            floorplan_url = tree.xpath(xp_floorplan_url)
            return floorplan_url[0] if floorplan_url else np.nan
        except Exception as e:
            logger.error(f"Error getting floorplan for {weblink}: {e}")
            return np.nan
