import csv
import time
from dataclasses import dataclass, fields, astuple
from urllib.parse import urljoin

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.common import (
    ElementNotInteractableException,
    NoSuchElementException,
)


BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")
SERVICE = ("/Users/bohdan_lysachenko/PycharmProjects/"
           "py-ecommerce-selenium-scraping/chromedriver_mac64/chromedriver")

URLS = {
    "home":
        "https://webscraper.io/test-sites/e-commerce/more",
    "computers":
        "https://webscraper.io/test-sites/e-commerce/more/computers",
    "laptops":
        "https://webscraper.io/test-sites/e-commerce/more/computers/laptops",
    "tablets":
        "https://webscraper.io/test-sites/e-commerce/more/computers/tablets",
    "phones":
        "https://webscraper.io/test-sites/e-commerce/more/phones",
    "touch":
        "https://webscraper.io/test-sites/e-commerce/more/phones/touch",
}


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


def get_single_product(product: WebElement) -> Product:
    return Product(
        title=product.find_element(By.CLASS_NAME, "title").get_attribute(
            "title"
        ),
        description=product.find_element(By.CLASS_NAME, "description").text,
        price=float(product.find_element(By.CLASS_NAME, "price").text[1:]),
        rating=len(product.find_elements(By.CLASS_NAME, "glyphicon-star")),
        num_of_reviews=int(
            product.find_element(By.CLASS_NAME, "ratings").text.split()[0]
        ),
    )


def parser(url: str) -> list[Product]:
    _driver.get(url)
    try:
        _driver.find_element(By.CLASS_NAME, "acceptCookies").click()
    except NoSuchElementException:
        pass
    while True:
        try:
            more = _driver.find_element(
                By.CSS_SELECTOR, ".ecomerce-items-scroll-more"
            )
            more.click()
            time.sleep(0.5)
        except (ElementNotInteractableException, NoSuchElementException):
            products = _driver.find_elements(By.CLASS_NAME, "thumbnail")
            return [get_single_product(product) for product in products]


def write_file(csv_path: str, products: list[Product]) -> None:
    with open(csv_path, "w") as file:
        writer = csv.writer(file)
        writer.writerow(PRODUCT_FIELDS)
        writer.writerows([astuple(product) for product in products])


def get_all_products() -> None:
    with webdriver.Chrome(SERVICE) as new_drier:
        for name, url in URLS.items():
            set_driver(new_drier)
            products = parser(url)
            write_file(f"{name}.csv", products)


if __name__ == "__main__":
    get_all_products()
