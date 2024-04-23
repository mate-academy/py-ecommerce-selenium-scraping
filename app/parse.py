import csv
import time

from dataclasses import dataclass, fields, asdict
from typing import List, Union
from urllib.parse import urljoin

from selenium.webdriver.remote.webelement import WebElement
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common import NoSuchElementException


BASE_URL = "https://webscraper.io/"


URLS = {
    "home": urljoin(
        BASE_URL,
        "test-sites/e-commerce/more/"
    ),
    "computers": urljoin(
        BASE_URL,
        "test-sites/e-commerce/more/computers"
    ),
    "laptops": urljoin(
        BASE_URL,
        "test-sites/e-commerce/more/computers/laptops"
    ),
    "tablets": urljoin(
        BASE_URL,
        "test-sites/e-commerce/more/computers/tablets"
    ),
    "phones": urljoin(
        BASE_URL,
        "test-sites/e-commerce/more/phones"
    ),
    "touch": urljoin(
        BASE_URL,
        "test-sites/e-commerce/more/phones/touch"
    ),
}


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


PRODUCT_FIELDS = [field.name for field in fields(Product)]


def parse_product(product: WebElement) -> Product:

    return Product(
        title=product.find_element(
            By.CSS_SELECTOR, ".caption > h4 > a"
        ).get_attribute("title"),
        description=product.find_element(
            By.CSS_SELECTOR, ".caption > .description"
        ).text,
        price=float(
            product.find_element(
                By.CSS_SELECTOR, ".caption > .price"
            ).text.replace("$", "")
        ),
        rating=len(
            product.find_elements(
                By.CSS_SELECTOR, ".ratings > p:nth-of-type(2) > span"
            )
        ),
        num_of_reviews=int(
            product.find_element(
                By.CSS_SELECTOR, ".ratings > .review-count"
            ).text.replace("reviews", "")
        ),
    )


def get_all_products_page(url: str) -> List[Product]:

    with webdriver.Chrome() as driver:
        driver.get(url)
        accept_cookies(driver)
        has_scroll_button(driver)
        products = driver.find_elements(By.CLASS_NAME, "thumbnail")
        return [parse_product(product) for product in products]


def accept_cookies(driver: WebElement) -> None:

    try:
        accept_button = driver.find_element(By.CLASS_NAME, "acceptCookies")
        accept_button.click()
    except NoSuchElementException:
        return


def scroll_page(driver: WebElement) -> None:

    while True:
        try:
            more_button = driver.find_element(
                By.CSS_SELECTOR, ".ecomerce-items-scroll-more"
            )
            if more_button.is_displayed():
                more_button.click()
                time.sleep(1)
            else:
                break
        except NoSuchElementException:
            break


def has_scroll_button(driver: WebElement) -> Union[list, bool]:

    try:
        scroll_page(driver)
        time.sleep(1)
    except NoSuchElementException:
        return False


def write_csv_file(file_name: str, products: List[Product]) -> None:

    with open(file_name, "w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(PRODUCT_FIELDS)
        writer.writerows([asdict(product).values() for product in products])


def get_all_products() -> None:

    for url in URLS:
        products = get_all_products_page(URLS[url])
        write_csv_file(f"{url}.csv", products)


if __name__ == "__main__":
    get_all_products()
