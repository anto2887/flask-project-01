import datetime
from flask import current_app
from app.scraper import table_scraper

def date_init():
    # Dictionary with the dates and corresponding 'n' values
    date_mapping = {
        '2023-10-24': 9,
        '2023-10-30': 10,
        '2023-11-07': 11,
        '2023-11-13': 12,
        '2023-11-26': 13,
        '2023-12-04': 14,
        '2023-12-07': 15,
        '2023-12-10': 16,
        '2023-12-17': 17,
        '2023-12-24': 18,
        '2023-12-27': 19,
        '2023-12-31': 20,
        '2024-01-14': 21,
        '2024-02-01': 22,
        '2024-02-04': 23,
        '2024-02-11': 24,
        '2024-02-18': 25,
        '2024-02-25': 26,
        '2024-03-03': 27,
        '2024-03-10': 28,
        '2024-03-17': 29,
        '2024-03-31': 30,
        '2024-04-04': 31,
        '2024-04-07': 32,
        '2024-04-14': 33,
        '2024-04-21': 34,
        '2024-04-28': 35,
        '2024-05-05': 36,
        '2024-05-12': 37,
        '2024-05-20': 38
    }

    # Get today's date
    today = datetime.date.today().strftime('%Y-%m-%d')

    # Check if today's date matches any key in the dictionary
    if today in date_mapping:
        n = date_mapping[today]
        current_app.logger.info(f"Scraping data for week number {n}")
        return table_scraper(n)
    else:
        current_app.logger.info("No scraping needed for today.")
        return None

    # Temporary bypass of date logic for testing
    # test_week_number = 10  # Set the week number you want to test
    # return table_scraper(test_week_number)