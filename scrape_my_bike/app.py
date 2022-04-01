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
BACKEND_URL = os.environ["BACKEND_URL"]
BACKEND_ADMIN_KEY = os.environ["BACKEND_ADMIN_KEY"]

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
            "Fahrrad", "Berlin", "Fahrräder & Zubehör", until=yesterday
        )

    batch_size = 2
    for i in range(0, len(image_urls), batch_size):
        batch = image_urls[i : (i + batch_size)]
        status_code, preds = _get_predictions(batch)
        if not status_code == 200:
            logging.error(f"Prediction endpoint returned {status_code}, not 200")
        else:
            for img_url, pred in zip(batch, preds):
                cleaned_pred = {k.replace("single_", ""): v for k, v in pred.items()}
                img_url["prediction"] = cleaned_pred
            status_code = _send_to_backend(batch)
            if not status_code == 200:
                logging.error(f"Backend returned {status_code}, not 201")

    return {
        "statusCode": 200,
        "body": json.dumps(image_urls, default=str),
    }


def _get_predictions(batch):
    payload = json.dumps([x["image_url"] for x in batch], default=str)
    headers = {"x-api-key": MODEL_API_KEY, "Content-Type": "application/json"}
    response = requests.post(MODEL_URL, headers=headers, data=payload)
    if response.status_code == 200:
        preds = json.loads(response.content)
    else:
        preds = []

    return response.status_code, preds


def _send_to_backend(batch):
    headers = {"access_token": BACKEND_ADMIN_KEY, "Content-Type": "application/json"}
    payload = json.dumps(batch, default=str)
    response = requests.post(BACKEND_URL, headers=headers, data=payload)

    return response.status_code
