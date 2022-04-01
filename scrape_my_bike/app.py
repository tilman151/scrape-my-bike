import json
import logging
import os
import sys
from datetime import date, timedelta

import requests
from selenium import webdriver

from scrape_my_bike import EbayImageScraper


CHROME_BINARY_LOC = os.environ["CHROME_BINARY_LOC"]
MODEL_URL = os.environ["MODEL_URL"]
MODEL_API_KEY = os.environ["MODEL_API_KEY"]

root = logging.getLogger()
root.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter("[%(asctime)s][%(name)s][%(levelname)s] - %(message)s")
handler.setFormatter(formatter)
root.addHandler(handler)

options = webdriver.ChromeOptions()
options.headless = True
options.binary_location = CHROME_BINARY_LOC
options.add_argument("--no-sandbox")
options.add_argument("--disable-gpu")
options.add_argument("--single-process")


def lambda_handler(event, context):
    yesterday = date.today() - timedelta(days=1)
    with EbayImageScraper(high_res=True, options=options) as scraper:
        image_urls = scraper.get_items(
            "Fahrrad", "Berlin", "Fahrräder & Zubehör", num=10
        )

    batch_size = 2
    for i in range(0, len(image_urls), batch_size):
        payload = json.dumps(
            [x["image_url"] for x in image_urls[i : (i + batch_size)]], default=str
        )
        headers = {"x-api-key": MODEL_API_KEY}
        response = requests.post(MODEL_URL, headers=headers, data=payload)
        preds = json.loads(response.content)
        for j, pred in enumerate(preds):
            cleaned_pred = {k.replace("single_", ""): v for k, v in pred.items()}
            image_urls[i + j]["prediction"] = cleaned_pred

    return {
        "statusCode": 200,
        "body": json.dumps(image_urls, default=str),
    }
