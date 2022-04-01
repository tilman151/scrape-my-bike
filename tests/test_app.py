import json
import os
from datetime import datetime
from unittest import mock

import pytest
import responses
from responses import matchers


@pytest.fixture
def env_vars(monkeypatch):
    monkeypatch.setenv("CHROME_BINARY_LOC", "")

    model_url = "https://foo.bar/predict"
    monkeypatch.setenv("MODEL_URL", model_url)
    model_api_key = "1234567890"
    monkeypatch.setenv("MODEL_API_KEY", model_api_key)

    backend_url = "https://foo.bar/postings"
    monkeypatch.setenv("BACKEND_URL", backend_url)
    backend_admin_key = "0987654321"
    monkeypatch.setenv("BACKEND_ADMIN_KEY", backend_admin_key)

    return model_url, model_api_key, backend_url, backend_admin_key


@pytest.fixture
def fake_preds(env_vars):
    model_url, model_api_key, backend_url, backend_admin_key = env_vars
    fake_preds = {"bike": "", "frame": "", "single_color": ""}
    expected_fake_preds = {"bike": "", "frame": "", "color": ""}
    today = str(datetime.now().date())
    responses.add(
        responses.POST,
        model_url,
        status=200,
        body=json.dumps([fake_preds, fake_preds]),
        match=[
            matchers.header_matcher(
                {"x-api-key": model_api_key, "Content-Type": "application/json"}
            ),
            matchers.json_params_matcher(["https://bar"] * 2),
        ],
    )
    responses.add(
        responses.POST,
        backend_url,
        status=201,
        match=[
            matchers.header_matcher(
                {"access_token": backend_admin_key, "Content-Type": "application/json"}
            ),
            matchers.json_params_matcher(
                [
                    {
                        "image_url": "https://bar",
                        "date": today,
                        "prediction": expected_fake_preds,
                    }
                ]
                * 2
            ),
        ],
    )

    return fake_preds


@responses.activate
def test_lambda_handler(fake_preds):
    from scrape_my_bike import app  # Import after setting env vars

    image_urls = [
        {"image_url": "https://bar", "date": datetime.now()},
        {"image_url": "https://bar", "date": datetime.now()},
        {"image_url": "https://bar", "date": datetime.now()},
        {"image_url": "https://bar", "date": datetime.now()},
    ]
    with mock.patch.object(app.EbayImageScraper, "get_items", return_value=image_urls):
        app.lambda_handler(None, None)
