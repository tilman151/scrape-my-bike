import json
import logging
from datetime import date, timedelta

from selenium import webdriver

from scrape_my_bike import EbayImageScraper

logging.basicConfig(filename='myapp.log', level=logging.INFO)

options = webdriver.ChromeOptions()
options.headless = True
options.binary_location = '/var/task/headless-chromium'
options.add_argument('--no-sandbox')
options.add_argument('--disable-gpu')
options.add_argument('--single-process')



def lambda_handler(event, context):
    yesterday = date.today() - timedelta(days=1)
    with EbayImageScraper(high_res=True, options=options) as scraper:
        image_urls = scraper.get_items(
            "Fahrrad", "Berlin", "Fahrräder & Zubehör", num=10
        )

    return {
        "statusCode": 200,
        "body": json.dumps(image_urls, default=str
        ),
    }
