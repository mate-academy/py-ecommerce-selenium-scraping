from selenium.webdriver.chrome.webdriver import WebDriver

from app.csv_file_creator import csv_file_creator
from app.config.parser_config import (
    TOP_COMPUTERS_URL,
    COMPUTERS_LAPTOPS_URL,
    COMPUTERS_TABLETS_URL
)
from app.scrappers.product_list_scrapper import get_product_list


def get_top_computer_page_products(driver: WebDriver) -> None:
    product_tuple = get_product_list(driver, TOP_COMPUTERS_URL)
    csv_file_creator("computers.csv", product_tuple)


def get_laptop_products(driver: WebDriver) -> None:
    product_tuple = get_product_list(driver, COMPUTERS_LAPTOPS_URL)
    csv_file_creator("laptops.csv", product_tuple)


def get_tablets_products(driver: WebDriver) -> None:
    product_tuple = get_product_list(driver, COMPUTERS_TABLETS_URL)
    csv_file_creator("tablets.csv", product_tuple)
