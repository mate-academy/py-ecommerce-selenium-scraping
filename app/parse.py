from __future__ import annotations

import csv
import time

from dataclasses import dataclass, fields, astuple

from urllib.parse import urljoin

from selenium import webdriver
from selenium.common import ElementNotInteractableException
from selenium.common import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement


BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")
COMPUTERS_URL = urljoin(HOME_URL, "computers")
LAPTOPS_URL = urljoin(HOME_URL, "computers/laptops")
TABLETS_URL = urljoin(HOME_URL, "computers/tablets")
PHONES_URL = urljoin(HOME_URL, "phones")
TOUCH_URL = urljoin(HOME_URL, "phones/touch")


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


def parse_one_product(product: WebElement) -> Product:
    return Product(
        title=product.find_element(
            By.CLASS_NAME, "title"
        ).get_attribute("title"),
        description=product.find_element(
            By.CLASS_NAME, "description"
        ).text,
        price=float(product.find_element(
            By.CLASS_NAME, "price"
        ).text.replace("$", "")),
        rating=len(product.find_elements(
            By.CLASS_NAME, "glyphicon-star"
        )),
        num_of_reviews=int(product.find_element(
            By.CSS_SELECTOR, ".ratings > .pull-right"
        ).text.split()[0])
    )


def parse_all_products(driver: WebDriver, url: str) -> list[Product]:
    driver.get(url)
    try:
        driver.find_element(By.CLASS_NAME, "acceptCookies").click()
    except NoSuchElementException:
        pass
    while True:
        try:
            scroll = driver.find_element(
                By.CSS_SELECTOR, ".ecomerce-items-scroll-more"
            )
            scroll.click()
            time.sleep(0.3)
        except (ElementNotInteractableException, NoSuchElementException):
            products = driver.find_elements(By.CLASS_NAME, "thumbnail")
            return [parse_one_product(product) for product in products]


def write_to_file(file_name: str, driver: WebDriver, url: str) -> None:
    all_products = parse_all_products(driver, url)
    with open(file_name, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(field.name for field in fields(Product))
        writer.writerows(astuple(product) for product in all_products)


def get_all_products() -> None:
    with webdriver.Chrome() as driver:
        write_to_file("home.csv", driver, HOME_URL)
        write_to_file("computers.csv", driver, COMPUTERS_URL)
        write_to_file("laptops.csv", driver, LAPTOPS_URL)
        write_to_file("tablets.csv", driver, TABLETS_URL)
        write_to_file("phones.csv", driver, PHONES_URL)
        write_to_file("touch.csv", driver, TOUCH_URL)


if __name__ == "__main__":
    get_all_products()
