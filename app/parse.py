import csv
import logging
import os
import sys
import time
from dataclasses import dataclass, fields, astuple
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from bs4.element import Tag
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver


BASE_URL = "https://webscraper.io/"
URLS = {
    "home": "test-sites/e-commerce/more/",
    "computers": "test-sites/e-commerce/more/computers",
    "laptops": "test-sites/e-commerce/more/computers/laptops",
    "tablets": "test-sites/e-commerce/more/computers/tablets",
    "phones": "test-sites/e-commerce/more/phones",
    "touch": "test-sites/e-commerce/more/phones/touch",
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

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ],
)


def get_driver() -> WebDriver:
    return _driver


def set_driver(new_driver: WebDriver) -> None:
    global _driver
    _driver = new_driver


def parce_single_product(product_soup: Tag) -> Product:
    return Product(
        title=product_soup.select_one(".title")["title"],
        description=product_soup.select_one(".description").text,
        price=float(product_soup.select_one(".price").text.replace("$", "")),
        rating=len(product_soup.select(
            ".ratings > :not(.review-count) > span"
        )),
        num_of_reviews=int(product_soup.select_one(
            ".ratings > p.review-count").text.split()[0]
        )
    )


def get_products(page_soup: BeautifulSoup) -> [Product]:
    products = page_soup.select(".product-wrapper")
    return [parce_single_product(product_soup) for product_soup in products]


def get_soup(url: str) -> BeautifulSoup:
    driver = get_driver()
    driver.get(url)

    try:
        cookie_accept_button = driver.find_element(
            By.CLASS_NAME, "acceptCookies"
        )
    except NoSuchElementException:
        logging.info("Accept cookie button not found")
    else:
        cookie_accept_button.click()

    try:
        more_button = driver.find_element(
            By.CSS_SELECTOR, ".ecomerce-items-scroll-more"
        )
    except NoSuchElementException:
        logging.info("More button not found")
    else:
        while more_button.is_displayed():
            more_button.click()
            time.sleep(0.05)

    page = driver.page_source
    soup = BeautifulSoup(page, "html.parser")

    return soup


def write_products_to_csv(filename: str, products: [Product]) -> None:
    with open(os.path.join(os.pardir, filename), "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(PRODUCT_FIELDS)
        writer.writerows([astuple(product) for product in products])


def get_all_products() -> None:
    options = webdriver.ChromeOptions()
    options.add_argument("headless")
    with webdriver.Chrome(options=options) as new_driver:
        set_driver(new_driver)
        for filename, url in URLS.items():
            filename += ".csv"
            url = urljoin(BASE_URL, url)
            soup = get_soup(url)
            products = get_products(soup)
            write_products_to_csv(filename, products)


def main() -> None:
    get_all_products()


if __name__ == "__main__":
    main()
