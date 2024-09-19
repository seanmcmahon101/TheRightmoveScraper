# The Rightmove Scraper

## Overview

This is an enhanced version of an existing Rightmove scraper, designed for improved performance and functionality.

## Key Features

- Utilizes multithreading for efficient scraping of floorplans
- Note: Floorplans are not always available for all properties

## Using This

- For now simply copy and paste the class into your code
- Will build the pip for this

## Use Case

Here's an example of how to use the Rightmove Scraper:

## Simple Use

```python
rm = TheRightmoveScraper(url, get_floorplans=True)
results = rm.get_results
```

```python
if __name__ == "__main__":
    url = "https://www.rightmove.co.uk/property-to-rent/find.html?locationIdentifier=REGION%5E94028&maxBedrooms=2&minBedrooms=2&maxPrice=1300&propertyTypes=flat&includeLetAgreed=false&mustHave=parking&dontShow=&furnishTypes=furnished&keywords="

    try:
        rm = TheRightmoveScraper(url, get_floorplans=True)
        results = rm.get_results
    except Exception as e:
        print(f"An error occurred while fetching data: {str(e)}")
        exit()

    print("All results:")
    print(results)
    print(f"\nTotal number of results: {len(results)}")

    excel_file = "rightmove_results.xlsx"
    try:
        results.to_excel(excel_file, index=False)
        print(f"\nResults saved to {excel_file}")
    except Exception as e:
        print(f"An error occurred while saving to Excel: {str(e)}")
        exit()

    try:
        if os.name == 'nt':
            os.startfile(excel_file)
        elif os.name == 'posix':
            import subprocess
            subprocess.call(['open', excel_file])
        print(f"\nOpened {excel_file}")
    except Exception as e:
        print(f"An error occurred while trying to open the file: {str(e)}")
        print(f"\nCould not automatically open {excel_file}. Please open it manually.")
```

## Functionality

1. **Data Fetching**: The script fetches property data from Rightmove based on the provided URL.
2. **Error Handling**: Robust error handling is implemented to catch and report any issues during data fetching.
3. **Results Display**: The script prints all fetched results and the total number of results.
4. **Excel Export**: Results are exported to an Excel file named "rightmove_results.xlsx".
5. **Automatic File Opening**: The script attempts to automatically open the Excel file after saving.

## Notes

- The script is designed to work on both Windows ('nt') and Unix-based ('posix') systems.
- If automatic file opening fails, a message is displayed prompting manual file opening.

## Requirements

- Python 3.x
- Required libraries: pandas (for Excel export), os (for file operations)
- For Unix-based systems: subprocess module for opening files

## Customization

You can customize the search parameters by modifying the URL in the script. The current URL is set to search for:
- 2-bedroom flats
- Maximum price of £1300
- Must have parking
- Furnished properties

## Create your URL

The easiest thing to is search on rightmove for your search, include any filters you want. Copy the URL after searching and paste it into the URL variable.

[Visit Rightmove](https://www.rightmove.co.uk/)
