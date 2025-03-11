import csv
import logging
import sys
from dataclasses import dataclass, fields, astuple
from urllib.parse import urljoin

from selenium import webdriver
from selenium.common import (
    ElementNotInteractableException,
    ElementClickInterceptedException,
    NoSuchElementException,
)
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")
COMPUTERS_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/computers/")
LAPTOPS_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/computers/laptops")
TABLETS_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/computers/tablets")
PHONES_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/phones/")
TOUCH_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/phones/touch")


_driver: WebDriver | None = None


options = Options()
options.add_argument("--headless")


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
    format="[%(levelname)8s]: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ],
)


def get_product(product: WebElement) -> Product:
    return Product(
        title=product.find_element(
            By.CLASS_NAME, "title"
        ).get_attribute("title"),
        description=product.find_element(
            By.CLASS_NAME, "description"
        ).text,
        price=float(product.find_element(
            By.CLASS_NAME, "price"
        ).text.strip("$")),
        rating=len(product.find_elements(
            By.CLASS_NAME, "ws-icon-star"
        )),
        num_of_reviews=int(
            product.find_element(
                By.CLASS_NAME, "review-count"
            ).text.split(" ")[0]
        ),
    )


def get_products(url: str) -> [Product]:
    driver = get_driver()
    driver.get(url)

    while True:
        try:
            logging.info("Clicking 'More' button")
            more_button = driver.find_element(By.CLASS_NAME, "btn")
            if more_button.is_displayed():
                more_button.click()
                accept_button = driver.find_element(
                    By.CLASS_NAME, "acceptCookies"
                )
                if accept_button:
                    accept_button.click()
            else:
                break
        except (
            NoSuchElementException,
            ElementNotInteractableException,
            ElementClickInterceptedException,
        ):
            logging.info("'More' button is not displayed")
            break
    logging.info("Started parsing page: %s ", url)
    products = driver.find_elements(By.CLASS_NAME, "card-body")
    all_products = [get_product(product) for product in products]
    logging.info("Ended parsing page: %s ", url)

    return all_products


def write_products_to_csv_file(
        products: [Product],
        csv_file_name: str
) -> None:
    with open(f"{csv_file_name}", "w", newline="") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(PRODUCT_FIELDS)
        logging.info(f"Started to write {csv_file_name}.csv file")
        writer.writerows([astuple(product) for product in products])


def get_all_products() -> None:
    pages = {
        "home": HOME_URL,
        "computers": COMPUTERS_URL,
        "laptops": LAPTOPS_URL,
        "tablets": TABLETS_URL,
        "phones": PHONES_URL,
        "touch": TOUCH_URL,
    }

    for page, url in pages.items():
        logging.info(f"Started to work with {page} page")
        write_products_to_csv_file(get_products(url), f"{page}.csv")
        logging.info(f"Data writing ended to {page}.csv file")


if __name__ == "__main__":
    with webdriver.Chrome(options=options) as driver:
        set_driver(driver)
        get_all_products()
