import csv
import logging
import sys
from dataclasses import dataclass, fields, astuple
from urllib.parse import urljoin

from selenium import webdriver
from selenium.common import NoSuchElementException, WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver


BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")
COMPUTER_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/computers/")
PHONE_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/phones/")
LAPTOP_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/computers/laptops")
TABLETS_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/computers/tablets")
TOUCH_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/phones/touch")

HOME_PRODUCTS_CSV_PATH = "home.csv"
COMPUTERS_PRODUCT_CSV_PATH = "computers.csv"
LAPTOPS_PRODUCT_CSV_PATH = "laptops.csv"
TABLETS_PRODUCT_CSV_PATH = "tablets.csv"
PHONES_PRODUCT_CSV_PATH = "phones.csv"
TOUCH_PRODUCTS_CSV_PATH = "touch.csv"


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


def accept_cookies(driver: WebDriver) -> None:
    try:
        cookies_button = driver.find_element(By.CLASS_NAME, "acceptCookies")
        cookies_button.click()
    except NoSuchElementException:
        return None


def click_more_button(driver: WebDriver) -> None:
    try:
        more_button = driver.find_element(By.LINK_TEXT, "More")
        while True:
            try:
                more_button.click()
            except WebDriverException:
                break
    except NoSuchElementException:
        return None


def get_detail_info(driver: WebDriver) -> [Product]:
    products = driver.find_elements(By.CLASS_NAME, "thumbnail")
    all_info = []
    for product in products:
        info = {
            "title": product.find_element(
                By.CSS_SELECTOR, "a.title"
            ).get_attribute("title"),
            "price": float(product.find_element(
                By.CLASS_NAME, "price"
            ).text.replace("$", "")),
            "description": product.find_element(
                By.CLASS_NAME, "description"
            ).text,
            "rating": len(
                product.find_elements(By.CLASS_NAME, "glyphicon-star")
            ),
            "num_of_reviews": int(
                product.find_element(
                    By.CSS_SELECTOR, ".ratings > .pull-right"
                ).text.split(" ")[0]
            ),
        }
        all_info.append(info)

    return [
        parse_single_product(product_info) for product_info in all_info
    ]


def parse_single_product(product_info: list) -> [Product]:
    product = Product(
        title=product_info["title"],
        description=product_info["description"],
        price=product_info["price"],
        rating=product_info["rating"],
        num_of_reviews=product_info["num_of_reviews"]
    )

    return product


def get_products(url: str) -> [Product]:
    driver = get_driver()
    driver.get(url)
    accept_cookies(driver)
    click_more_button(driver)

    return get_detail_info(driver)


def get_all_products() -> None:
    with webdriver.Chrome() as new_driver:
        set_driver(new_driver)
        products = {
            HOME_PRODUCTS_CSV_PATH: get_products(HOME_URL),
            COMPUTERS_PRODUCT_CSV_PATH: get_products(COMPUTER_URL),
            PHONES_PRODUCT_CSV_PATH: get_products(PHONE_URL),
            LAPTOPS_PRODUCT_CSV_PATH: get_products(LAPTOP_URL),
            TABLETS_PRODUCT_CSV_PATH: get_products(TABLETS_URL),
            TOUCH_PRODUCTS_CSV_PATH: get_products(TOUCH_URL)
        }
        write_products_to_cvs(products)


def write_products_to_cvs(products: [Product]) -> None:
    for csv_path, product_type in products.items():
        with open(csv_path, "w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(PRODUCT_FIELDS)
            writer.writerows([astuple(product) for product in product_type])


if __name__ == "__main__":
    get_all_products()
