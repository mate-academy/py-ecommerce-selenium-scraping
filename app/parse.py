import csv
from dataclasses import dataclass, fields, astuple
from typing import List
from urllib.parse import urljoin
from selenium.common import (NoSuchElementException,
                             ElementNotInteractableException,
                             ElementClickInterceptedException)
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")
URLS_FOR_PARSING = {
    "home": HOME_URL,
    "computers": urljoin(HOME_URL, "computers"),
    "laptops": urljoin(HOME_URL, "computers/laptops"),
    "tablets": urljoin(HOME_URL, "computers/tablets"),
    "phones": urljoin(HOME_URL, "phones"),
    "touch": urljoin(HOME_URL, "phones/touch")
}


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


PRODUCT_FIELDS = [field.name for field in fields(Product)]


web_driver = WebDriver()


def parse_single_product(product: WebElement) -> Product:
    return Product(
        title=product.find_element(By.CLASS_NAME,
                                   "title").get_attribute("title"),
        description=product.find_element(By.CLASS_NAME,
                                         "description").text,
        price=float(product.find_element(By.CLASS_NAME,
                                         "price").text.replace("$", "")),
        rating=len(product.find_elements(By.CLASS_NAME,
                                         "ws-icon-star")),
        num_of_reviews=int(product.find_element(By.CLASS_NAME,
                                                "ratings").text.split()[0]))


def get_all_products_from_url(url: str) -> List[Product]:
    driver = web_driver
    driver.get(url)

    if cookies := driver.find_elements(By.CLASS_NAME,
                                       "acceptCookies"):
        cookies[0].click()

    while True:
        try:
            driver.find_element(By.CLASS_NAME,
                                "ecomerce-items-scroll-more").click()
        except (
            NoSuchElementException,
            ElementNotInteractableException,
            ElementClickInterceptedException,
        ):
            break

    products = driver.find_elements(By.CLASS_NAME, "product-wrapper")
    return [parse_single_product(product) for product in products]


def write_to_file(products: List[Product], filename: str) -> None:
    with open(filename + ".csv", "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(PRODUCT_FIELDS)
        writer.writerows([astuple(product) for product in products])


def get_all_products() -> None:
    for csv_name, url in URLS_FOR_PARSING.items():
        write_to_file(get_all_products_from_url(url), csv_name)


if __name__ == "__main__":
    get_all_products()
