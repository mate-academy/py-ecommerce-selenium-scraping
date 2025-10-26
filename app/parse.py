import csv
import logging
import sys
import time
from dataclasses import dataclass, fields, asdict
from typing import List
from urllib.parse import urljoin

from selenium import webdriver
from selenium.common.exceptions import (
    NoSuchElementException,
    ElementNotInteractableException
)
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.wait import WebDriverWait
from tqdm import tqdm

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")

FILENAME_URL_MAP = {
    "home": "",
    "computers": "computers",
    "laptops": "computers/laptops",
    "tablets": "computers/tablets",
    "phones": "phones",
    "touch": "phones/touch",
}

_driver: WebDriver | None = None


def get_driver() -> WebDriver:
    return _driver


def set_driver(new_driver: WebDriver) -> None:
    global _driver
    _driver = new_driver


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


PRODUCT_FIELDS = [field.name for field in fields(Product)]

logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)8s]:  %(message)s",
    handlers=[
        logging.FileHandler("parser_selenium.log"),
        logging.StreamHandler(sys.stdout),
    ],
)


def parse_single_product(product_card: WebElement) -> Product:
    return Product(
        title=product_card.find_element(
            By.CLASS_NAME, "title"
        ).get_property("title"),
        description=product_card.find_element(
            By.CLASS_NAME, "description"
        ).text,
        price=float(
            product_card.find_element(
                By.CLASS_NAME, "price"
            ).text.replace("$", "")
        ),
        rating=len(
            product_card.find_elements(By.CLASS_NAME, "ws-icon-star")
        ),
        num_of_reviews=int(
            product_card.find_element(
                By.CSS_SELECTOR, '[itemprop="reviewCount"]'
            ).text
        ),
    )


def get_page_products(page_url: str) -> List[Product]:
    driver = get_driver()
    wait = WebDriverWait(driver, 60)

    page_url = urljoin(HOME_URL, page_url)
    logging.info(f"Start parsing /{page_url}")
    driver.get(page_url)
    wait.until(ec.presence_of_element_located((By.CLASS_NAME, "card")))

    try:
        cookie_accept_button = driver.find_element(
            By.CLASS_NAME, "acceptCookies"
        )
        cookie_accept_button.click()
        logging.info("Pressed 'Accept Cookie' button.")
        time.sleep(0.5)
    except NoSuchElementException:
        pass

    try:
        while True:
            more_button = driver.find_element(
                By.CLASS_NAME, "ecomerce-items-scroll-more"
            )
            more_button.click()
            logging.info("Pressed 'More' button to get more items.")
            time.sleep(0.5)
    except (NoSuchElementException, ElementNotInteractableException):
        pass

    products = []
    product_cards = driver.find_elements(By.CLASS_NAME, "card")

    for product_card in tqdm(
            product_cards,
            desc=f"Getting products from {page_url}"
    ):
        products.append(parse_single_product(product_card))

    return products


def write_products_to_csv(filename: str, products: List[Product]) -> None:
    with open(filename, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=PRODUCT_FIELDS)
        writer.writeheader()
        for product in tqdm(products, desc=f"Writing products to {filename}"):
            writer.writerow(asdict(product))


def get_all_products() -> None:
    options = Options()
    options.add_argument("--headless")
    with webdriver.Chrome(options=options) as driver:
        set_driver(driver)
        for filename, url in FILENAME_URL_MAP.items():
            products = get_page_products(url)
            write_products_to_csv(f"{filename}.csv", products)


if __name__ == "__main__":
    get_all_products()
