import csv
import time
from dataclasses import dataclass, fields, astuple
from urllib.parse import urljoin

from selenium import webdriver
from selenium.common import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")

PRODUCTS_URLS_AND_OUTPUT_CSV_PATH = [
    (HOME_URL, "home.csv"),
    (urljoin(HOME_URL, "computers"), "computers.csv"),
    (urljoin(HOME_URL, "computers/laptops"), "laptops.csv"),
    (urljoin(HOME_URL, "computers/tablets"), "tablets.csv"),
    (urljoin(HOME_URL, "phones"), "phones.csv"),
    (urljoin(HOME_URL, "phones/touch"), "touch.csv"),
]


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


PRODUCT_FIELDS = [field.name for field in fields(Product)]

_driver: WebDriver | None = None


def get_driver() -> WebDriver:
    return _driver


def set_driver(new_driver: WebDriver) -> None:
    global _driver
    _driver = new_driver


def parse_single_product(product: WebElement) -> Product:
    return Product(
        title=product.find_element(
            By.CLASS_NAME, "title").get_attribute("title"),
        description=product.find_element(By.CLASS_NAME, "description").text,
        price=float(product.find_element(
            By.CLASS_NAME, "price").text.replace("$", "")),
        rating=int(
            len(product.find_elements(By.CLASS_NAME, "glyphicon-star"))
        ),
        num_of_reviews=int(
            product.find_element(
                By.CSS_SELECTOR, ".ratings .pull-right"
            ).text.split()[0]
        ),
    )


def write_products_to_csv(products: [Product], csv_path: str) -> None:
    with open(csv_path, "w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(PRODUCT_FIELDS)
        writer.writerows([astuple(product) for product in products])


def get_all_products() -> None:
    with webdriver.Chrome() as new_driver:
        set_driver(new_driver)
        for page_url, csv_path in PRODUCTS_URLS_AND_OUTPUT_CSV_PATH:
            driver = get_driver()
            driver.get(page_url)

            try:
                cookies = driver.find_element(By.CLASS_NAME, "acceptCookies")
                cookies.click()
            except NoSuchElementException:
                pass

            try:
                more_button = driver.find_element(
                    By.CLASS_NAME, "ecomerce-items-scroll-more"
                )
            except NoSuchElementException:
                pass
            else:
                while more_button.is_displayed():
                    more_button.click()
                    time.sleep(0.2)

            products = driver.find_elements(By.CLASS_NAME, "thumbnail")
            products_list = [
                parse_single_product(product) for product in products
            ]

            write_products_to_csv(products_list, csv_path)


if __name__ == "__main__":
    get_all_products()
