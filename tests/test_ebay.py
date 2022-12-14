from datetime import date, datetime, timedelta
from unittest import mock

import pytz

from scrape_my_bike.ebay import EbayImageScraper


@mock.patch("scrape_my_bike.ebay.webdriver")
def test_driver_init(mock_webdriver):
    scraper = EbayImageScraper()
    mock_webdriver.Chrome.assert_called_once_with(
        options=mock_webdriver.ChromeOptions()
    )
    assert scraper.driver is mock_webdriver.Chrome()


@mock.patch("scrape_my_bike.ebay.webdriver")
def test_context_manager(mock_webdriver):
    scraper = EbayImageScraper()
    with scraper as context_scraper:
        assert scraper is context_scraper
    mock_webdriver.Chrome().quit.assert_called_once()


def test_retrieving_items():
    with EbayImageScraper() as scraper:
        items = scraper.get_items("Fahrrad", "Berlin", "Fahrräder & Zubehör", 30)
    assert len(items) == 30
    assert "url" in items[0]
    assert "image_url" in items[0]
    assert "query" in items[0]
    assert "location" in items[0]


def test_retrieving_items_until():
    last_hour = datetime.now(pytz.timezone("Europe/Berlin")) - timedelta(hours=1)
    with EbayImageScraper() as scraper:
        items = scraper.get_items(
            "Fahrrad", "Berlin", "Fahrräder & Zubehör", until=last_hour
        )
    assert "url" in items[0]
    assert "image_url" in items[0]
    assert "query" in items[0]
    assert "location" in items[0]
    assert "date" in items[0]
    assert items[-1]["date"] > last_hour


def test_high_res_image_urls():
    with EbayImageScraper(high_res=True) as scraper:
        items = scraper.get_items("Fahrrad", "Berlin", "Fahrräder & Zubehör", 1)
    assert items[0]["image_url"].endswith("$_59.JPG")  # URL for highres image


@mock.patch.object(EbayImageScraper, "_get_until_items")
@mock.patch.object(EbayImageScraper, "_get_num_items")
def test_number_of_items_configuration(mock_get_num, mock_get_until):
    with EbayImageScraper() as scraper:
        scraper.get_items("Fahrrad", "Berlin", "Fahrräder & Zubehör", num=30)
    mock_get_num.assert_called_with(30, "Fahrrad", "Berlin")

    with EbayImageScraper() as scraper:
        scraper.get_items(
            "Fahrrad", "Berlin", "Fahrräder & Zubehör", until=date.today()
        )
    mock_get_until.assert_called_with(date.today(), "Fahrrad", "Berlin")
