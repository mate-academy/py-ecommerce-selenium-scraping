from selenium.webdriver.chrome.webdriver import WebDriver

from app.config.parser_config import (
    TOP_PHONES_URL,
    PHONES_TOUCH_URL,
)
from app.csv_file_creator import csv_file_creator
from app.scrappers.product_list_scrapper import get_product_list


def get_top_phone_page_products(driver: WebDriver) -> None:
    product_tuple = get_product_list(driver, TOP_PHONES_URL)
    csv_file_creator("phones.csv", product_tuple)


def get_phone_touch_with_pagination_products(driver: WebDriver) -> None:
    product_tuple = get_product_list(driver, PHONES_TOUCH_URL)
    csv_file_creator("touch.csv", product_tuple)
