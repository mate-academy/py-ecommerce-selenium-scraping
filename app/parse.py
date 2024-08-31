import csv
import time
from dataclasses import (
    dataclass,
    fields,
    astuple
)
from typing import List
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup, Tag
from selenium import webdriver
from selenium.common import (
    NoSuchElementException,
    ElementClickInterceptedException
)
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By


BASE_URL = "https://webscraper.io/"

# All urls with products for parsing
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")
COMPUTERS_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/computers")
LAPTOPS_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/computers/laptops")
TABLETS_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/computers/tablets")
PHONES_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/phones")
TOUCH_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/phones/touch")

# All csv paths
HOME_CSV_PATH = "home.csv"
COMPUTERS_CSV_PATH = "computers.csv"
LAPTOPS_CSV_PATH = "laptops.csv"
TABLETS_CSV_PATH = "tablets.csv"
PHONES_CSV_PATH = "phones.csv"
TOUCH_CSV_PATH = "touch.csv"


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


def set_driver(
        new_driver: WebDriver
) -> None:

    global _driver
    _driver = new_driver


def parse_single_product(
        product_soup: Tag, is_paginated: bool = False
) -> Product:

    if not is_paginated:
        rating = int(product_soup.select_one("p[data-rating]")["data-rating"])
    else:
        rating = len(product_soup.select(".ratings .ws-icon.ws-icon-star"))

    return Product(
        title=product_soup.select_one(
            ".title"
        )["title"],
        description=product_soup.select_one(
            ".description"
        ).text.replace("\xa0", " ").strip(),
        price=float(product_soup.select_one(
            ".price"
        ).text.replace("$", "")),
        rating=rating,
        num_of_reviews=int(product_soup.select_one(
            ".ratings > p.review-count"
        ).text.split()[0]),
    )


def get_single_page_products(
        page_soup: BeautifulSoup, is_paginated: bool = False
) -> List[Product]:

    products = page_soup.select(".product-wrapper")
    return [
        parse_single_product(product, is_paginated) for product in products
    ]


def get_products(url: str) -> List[Product]:
    response = requests.get(url)
    response.raise_for_status()

    page_soup = BeautifulSoup(response.text, "html.parser")
    return get_single_page_products(page_soup, False)


def get_products_with_pagination(
        driver: webdriver.Chrome, url: str
) -> List[Product]:

    driver.get(url)
    all_products = []

    while True:
        page_soup = BeautifulSoup(driver.page_source, "html.parser")
        new_products = get_single_page_products(page_soup, is_paginated=True)
        all_products.extend(
            product for product in new_products if product not in all_products
        )

        try:
            more_button = driver.find_element(
                By.CLASS_NAME, "ecomerce-items-scroll-more"
            )
            if not more_button.is_displayed():
                break
            driver.execute_script(
                "arguments[0].scrollIntoView(true);", more_button
            )
            time.sleep(1)

            try:
                more_button.click()
                time.sleep(2)
            except ElementClickInterceptedException:
                break

        except NoSuchElementException:
            break

    return all_products


def write_products_to_csv(
        products: List[Product], product_path: str
) -> None:

    with open(product_path, "w") as file:
        writer = csv.writer(file)
        writer.writerow(PRODUCT_FIELDS)
        writer.writerows([astuple(product) for product in products])


def get_all_products() -> None:
    write_products_to_csv(get_products(HOME_URL), HOME_CSV_PATH)
    write_products_to_csv(get_products(COMPUTERS_URL), COMPUTERS_CSV_PATH)
    write_products_to_csv(get_products(PHONES_URL), PHONES_CSV_PATH)

    driver = webdriver.Chrome()
    try:
        write_products_to_csv(
            get_products_with_pagination(driver, LAPTOPS_URL), LAPTOPS_CSV_PATH
        )
        write_products_to_csv(
            get_products_with_pagination(driver, TABLETS_URL), TABLETS_CSV_PATH
        )
        write_products_to_csv(
            get_products_with_pagination(driver, TOUCH_URL), TOUCH_CSV_PATH
        )
    finally:
        driver.close()


if __name__ == "__main__":
    get_all_products()
