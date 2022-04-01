import json
import os
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

    return model_url, model_api_key


@pytest.fixture
def fake_preds(env_vars):
    model_url, model_api_key = env_vars
    fake_preds = {"bike": "", "frame": "", "single_color": ""}
    responses.add(
        responses.POST,
        model_url,
        body=json.dumps([fake_preds, fake_preds]),
        match=[matchers.header_matcher({"x-api-key": model_api_key})],
    )

    return fake_preds


@responses.activate
def test_lambda_handler(fake_preds):
    from scrape_my_bike import app  # Import after setting env vars

    with mock.patch.object(
        app.EbayImageScraper,
        "get_items",
        return_value=[
            {"image_url": "https://bar"},
            {"image_url": "https://bar"},
            {"image_url": "https://bar"},
            {"image_url": "https://bar"},
        ],
    ):
        response = app.lambda_handler(None, None)

    assert "body" in response
    assert isinstance(response["body"], str)
    expected_fake_preds = {k.replace("single_", ""): v for k, v in fake_preds.items()}
    for item in json.loads(response["body"]):
        assert "prediction" in item
        assert item["prediction"] == expected_fake_preds
