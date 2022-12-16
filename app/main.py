from app.parse import Product, PRODUCT_FIELDS, get_single_page_product
import csv
from dataclasses import astuple
from urllib.parse import urljoin
from selenium import webdriver
from selenium.webdriver.remote.webdriver import WebDriver


BASE_URL = "https://webscraper.io"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")
LIST_URLS = [
    (HOME_URL, "home.csv"),
    (urljoin(HOME_URL, "computers"), "computers.csv"),
    (urljoin(HOME_URL, "computers/laptops"), "laptops.csv"),
    (urljoin(HOME_URL, "computers/tablets"), "tablets.csv"),
    (urljoin(HOME_URL, "phones"), "phones.csv"),
    (urljoin(HOME_URL, "phones/touch"), "touch.csv"),
]


class ChromeDriver:
    def __init__(self) -> None:
        self.__driver = webdriver.Chrome()

    @property
    def get_driver(self) -> WebDriver:
        return self.__driver


def write_products_to_csv(products: [Product], output_csv_path: str) -> None:
    with open(output_csv_path, "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(PRODUCT_FIELDS)
        writer.writerows([astuple(product) for product in products])


def get_all_products() -> None:
    with webdriver.Chrome() as driver:
        for url in LIST_URLS:
            write_products_to_csv(
                get_single_page_product(driver, url[0]), url[1]
            )


if __name__ == "__main__":
    get_all_products()
