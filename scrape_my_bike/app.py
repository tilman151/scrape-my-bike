import json
import logging
import os
import sys
from datetime import timedelta, datetime, tzinfo, timezone
from tempfile import mkdtemp

import pytz as pytz
import requests
from selenium import webdriver

from scrape_my_bike import EbayImageScraper


CHROME_BINARY_LOC = os.environ["CHROME_BINARY_LOC"]
MODEL_URL = os.environ["MODEL_URL"]
MODEL_API_KEY = os.environ["MODEL_API_KEY"]
BACKEND_URL = os.environ["BACKEND_URL"]
BACKEND_ADMIN_KEY = os.environ["BACKEND_ADMIN_KEY"]

logger = logging.getLogger()
logger.setLevel(logging.INFO)

options = webdriver.ChromeOptions()
options.headless = True
options.binary_location = CHROME_BINARY_LOC
options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--disable-gpu")
options.add_argument("--window-size=1280x1696")
options.add_argument("--single-process")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-dev-tools")
options.add_argument("--no-zygote")
options.add_argument(f"--user-data-dir={mkdtemp()}")
options.add_argument(f"--data-path={mkdtemp()}")
options.add_argument(f"--disk-cache-dir={mkdtemp()}")
options.add_argument("--remote-debugging-port=9222")


def lambda_handler(event, context):
    last_hour = datetime.now(pytz.timezone("Europe/Berlin")) - timedelta(hours=1)
    with EbayImageScraper(high_res=True, options=options) as scraper:
        image_urls = scraper.get_items(
            "Fahrrad", "Berlin", "Fahrräder & Zubehör", until=last_hour
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
            batch = list(filter(_is_bike, batch))
            status_code = _send_to_backend(batch)
            if not status_code == 201:
                logging.error(f"Backend returned {status_code}, not 201")

    return {"statusCode": 200}


def _is_bike(x):
    return not x["prediction"]["bike"] == "no_bike"


def _get_predictions(batch):
    payload = [x["image_url"] for x in batch]
    logger.info(f"Predict {payload}")
    payload = json.dumps(payload, default=str)
    headers = {"x-api-key": MODEL_API_KEY}
    response = requests.post(MODEL_URL, headers=headers, data=payload)
    if response.status_code == 200:
        preds = json.loads(response.content)
    else:
        preds = []

    return response.status_code, preds


def _send_to_backend(batch):
    if batch:
        logger.info(f"Send to backend {[x['image_url'] for x in batch]}")
        headers = {
            "access_token": BACKEND_ADMIN_KEY,
            "Content-Type": "application/json",
        }
        payload = json.dumps({"data": batch}, default=lambda d: str(d.date()))
        response = requests.post(BACKEND_URL, headers=headers, data=payload)
        status_code = response.status_code
    else:
        status_code = 201

    return status_code
