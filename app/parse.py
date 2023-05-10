import time
from contextlib import contextmanager
from urllib.parse import urljoin
import csv
from dataclasses import dataclass, fields, astuple
from typing import List

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")

URLS = [
    ("home", ""),
    ("computers", "computers"),
    ("laptops", "computers/laptops"),
    ("tablets", "computer/tablets"),
    ("phones", "phones"),
    ("touch", "phones/touch"),
]


@contextmanager
def chrome_driver() -> None:
    driver = webdriver.Chrome()
    try:
        yield driver
    finally:
        driver.quit()


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


PRODUCT_FIELDS = [field.name for field in fields(Product)]


def get_single_product(product: WebElement) -> Product:
    title = product.find_element(By.CLASS_NAME, "title").get_attribute("title")
    description = product.find_element(By.CLASS_NAME, "description").text
    price = float(
        product.find_element(By.CLASS_NAME, "price").text.replace("$", "")
    )
    rating = len(product.find_elements(By.CLASS_NAME, "glyphicon-star"))
    num_of_reviews = int(
        product.find_element(By.CLASS_NAME, "ratings").text.split()[0]
    )
    return Product(title, description, price, rating, num_of_reviews)


def get_single_page_products(driver: webdriver, url: str) -> List[Product]:
    products = []
    products_url = urljoin(HOME_URL, url)
    driver.get(products_url)
    cookies = driver.find_elements(By.CLASS_NAME, "acceptCookies")
    if cookies:
        cookies[0].click()
    buttons = driver.find_elements(By.CLASS_NAME, "ecomerce-items-scroll-more")
    if buttons:
        button = buttons[0]
        while button.is_displayed():
            button.click()
            time.sleep(0.2)
    for product in driver.find_elements(By.CLASS_NAME, "thumbnail"):
        product = get_single_product(product)
        products.append(product)

    return products


def write_to_csv(filename: str, products: List[Product]) -> None:
    with open(f"{filename}.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(PRODUCT_FIELDS)
        writer.writerows([astuple(product) for product in products])


def get_all_products() -> None:
    with chrome_driver() as new_driver:
        for name, url in URLS:
            products = get_single_page_products(new_driver, url)
            write_to_csv(name, products)


if __name__ == "__main__":
    get_all_products()
