import csv
import time
from dataclasses import dataclass, fields, astuple
from typing import List
from urllib.parse import urljoin

from selenium import webdriver
from selenium.common.exceptions import (
    NoSuchElementException,
    ElementNotInteractableException
)
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from tqdm import tqdm

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")
PARSE_URLS = {
    "home": urljoin(BASE_URL, "test-sites/e-commerce/more"),
    "computers": urljoin(BASE_URL, "test-sites/e-commerce/more/computers"),
    "laptops": urljoin(
        BASE_URL,
        "test-sites/e-commerce/more/computers/laptops"
    ),
    "tablets": urljoin(
        BASE_URL,
        "test-sites/e-commerce/more/computers/tablets"
    ),
    "phones": urljoin(BASE_URL, "test-sites/e-commerce/more/phones"),
    "touch": urljoin(BASE_URL, "test-sites/e-commerce/more/phones/touch"),
}


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


PRODUCT_FIELDS = [field.name for field in fields(Product)]


def parse_single_product(product: WebElement) -> Product:
    return Product(
        title=product.find_element(
            By.CLASS_NAME, "title"
        ).get_property("title"),
        description=product.find_element(By.CLASS_NAME, "description").text,
        price=float(
            product.find_element(By.CLASS_NAME, "price").text.replace("$", "")
        ),
        rating=len(product.find_elements(By.CLASS_NAME, "ws-icon-star")),
        num_of_reviews=int(
            product.find_element(By.CLASS_NAME, "review-count").text.split()[0]
        ),
    )


def parse_single_page(url: str, driver: webdriver.Chrome) -> List[Product]:
    driver.get(url)
    products = []

    try:
        cookie_button = driver.find_elements(By.CLASS_NAME, "acceptCookies")
        if cookie_button:
            cookie_button[0].click()
    except (NoSuchElementException, ElementNotInteractableException):
        pass

    while True:
        try:
            scroll_button = driver.find_element(
                By.CLASS_NAME, "btn.btn-primary.btn-lg.btn-block"
            )
            if scroll_button.is_displayed():
                scroll_button.click()
                time.sleep(1)
            else:
                break
        except (NoSuchElementException, ElementNotInteractableException):
            break

    product_elements = driver.find_elements(By.CLASS_NAME, "thumbnail")

    with tqdm(total=len(product_elements), ncols=100) as pbar:
        for product_element in product_elements:
            products.append(parse_single_product(product_element))
            pbar.update(1)

    return products


def write_to_csv(filename: str, products: List[Product]) -> None:
    with open(filename + ".csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(PRODUCT_FIELDS)
        writer.writerows([astuple(product) for product in products])


def get_all_products() -> None:
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    driver = webdriver.Chrome(options=chrome_options)

    with tqdm(total=len(PARSE_URLS), ncols=100) as pbar:
        for name, url in PARSE_URLS.items():
            all_products = parse_single_page(url, driver)
            write_to_csv(name, all_products)
            pbar.update(1)

    driver.quit()


if __name__ == "__main__":
    get_all_products()
