import csv
import logging
import sys
from dataclasses import dataclass, fields, astuple
import time
from urllib.parse import urljoin

from selenium import webdriver
from selenium.common import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement

BASE_URL = "https://webscraper.io/test-sites/e-commerce/more/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")

PAGES = {
    "home": BASE_URL,
    "computers": urljoin(BASE_URL, "computers/"),
    "laptops": urljoin(BASE_URL, "computers/laptops"),
    "tablets": urljoin(BASE_URL, "computers/tablets"),
    "phones": urljoin(BASE_URL, "phones/"),
    "touch": urljoin(BASE_URL, "phones/touch"),
}


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


QUOTE_FIELDS = [field.name for field in fields(Product)]

_driver: WebDriver | None = None


def get_driver() -> WebDriver:
    return _driver


def set_driver(new_driver: WebDriver) -> None:
    global _driver
    _driver = new_driver


logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] - [%(levelname)8s]: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("parser.log"),
    ]
)


def get_additional_info():
    ...
    # additional info about products
    # not implemented


def parse_single_product(element: WebElement) -> Product:
    return Product(
        title=element.find_element(
            By.CSS_SELECTOR, ".title"
        )
        .get_attribute("title"),
        description=(
            element.find_element(
                By.CSS_SELECTOR, ".description"
            )
            .text
        ),
        price=float(
            element
            .find_element(By.CSS_SELECTOR, ".price")
            .text.replace("$", "")
        ),
        rating=len(element.find_elements(By.CSS_SELECTOR, ".ws-icon-star")),
        num_of_reviews=int(
            element
            .find_element(By.CSS_SELECTOR, ".review-count")
            .text.split()[0]
        )
    )


def close_cookie_banner() -> None:
    driver = get_driver()
    close_btn = driver.find_element(By.ID, "closeCookieBanner")
    close_btn.click()


def load_page(url: str) -> WebDriver:
    driver = get_driver()
    driver.get(url)
    time.sleep(1)
    close_cookie_banner()
    try:
        load_btn = driver.find_element(
            By.CLASS_NAME, "ecomerce-items-scroll-more"
        )
        logging.info(f"Loading page {url}...")
        while load_btn.is_displayed():
            load_btn.click()
            time.sleep(0.1)
    except NoSuchElementException:
        logging.info(f"Cand load more on {url}")

    return driver


def get_all_products() -> None:
    with webdriver.Chrome() as new_driver:
        set_driver(new_driver)
        logging.info("Start parsing")
        for category, url in PAGES.items():
            page = load_page(url)

            logging.info(f"Finding elements for {category}...")
            elements = page.find_elements(
                By.CLASS_NAME, "thumbnail"
            )

            logging.info(f"Parsing each product for {category}...")
            products = [
                parse_single_product(element)
                for element in elements
            ]

            write_products_to_csv(f"{category}.csv", products)


def write_products_to_csv(
        file_path: str,
        products: list[Product],
) -> None:
    with open(file_path, "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(QUOTE_FIELDS)
        writer.writerows([astuple(product) for product in products])

    logging.info(f"File {file_path} was written")


if __name__ == "__main__":
    get_all_products()
