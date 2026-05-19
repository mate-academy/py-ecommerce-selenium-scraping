from selenium.webdriver.chrome.webdriver import WebDriver

from app.csv_file_creator import csv_file_creator
from app.config.parser_config import HOME_URL
from app.scrappers.product_list_scrapper import get_product_list


def get_home_page_products(driver: WebDriver) -> None:
    product_tuple = get_product_list(driver, HOME_URL)
    csv_file_creator("home.csv", product_tuple)
