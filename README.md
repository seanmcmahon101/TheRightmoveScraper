#The Rightmove Scraper

##Something like this already exists. This is just more performative.

###Using multithreading for the scraping of floorplans. Note: Floorplans arent always available.

###Use Case
'''
if __name__ == "__main__":
    url = "https://www.rightmove.co.uk/property-to-rent/find.html?locationIdentifier=REGION%5E94028&maxBedrooms=2&minBedrooms=2&maxPrice=1300&propertyTypes=flat&includeLetAgreed=false&mustHave=parking&dontShow=&furnishTypes=furnished&keywords="

    try:
        rm = RightmoveData(url, get_floorplans=True)
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
        '''
