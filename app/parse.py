import csv
import time

from dataclasses import dataclass, fields, asdict
from typing import List
from urllib.parse import urljoin

from selenium.webdriver.remote.webelement import WebElement
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common import NoSuchElementException


BASE_URL = "https://webscraper.io/"


URLS = {
    "home": urljoin(BASE_URL, "test-sites/e-commerce/more/"),
    "computers": urljoin(BASE_URL, "test-sites/e-commerce/more/computers"),
    "laptops": urljoin(BASE_URL, "test-sites/e-commerce/more/computers/laptops"),
    "tablets": urljoin(BASE_URL, "test-sites/e-commerce/more/computers/tablets"),
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
    """
    Parse data of a single product.
    """

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


def get_page_with_products(url: str) -> List[Product]:
    """
    Get the list of products on the page.
    """
    with webdriver.Chrome() as driver:
        driver.get(url)
        accept_cookies(driver)
        resolve_scroll_button(driver)
        products = driver.find_elements(By.CLASS_NAME, "thumbnail")

        return [parse_single_product(product) for product in products]


def accept_cookies(driver: WebElement) -> None:
    """
    Click on the cookies acceptance button.
    """
    try:
        accept_button = driver.find_element(By.CLASS_NAME, "acceptCookies")
        accept_button.click()
    except NoSuchElementException:
        return


def scroll_page(driver: WebElement) -> None:
    """
    Scroll the page to load more products.
    """
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


def resolve_scroll_button(driver: WebElement) -> bool:
    """
    Check if the scroll button is present.
    """
    try:
        scroll_page(driver)
        time.sleep(1)
    except NoSuchElementException:
        return False


def write_to_csv(file_name: str, products: List[Product]) -> None:
    """
    Write data to a CSV file.
    """
    with open(file_name, "w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(PRODUCT_FIELDS)
        writer.writerows([asdict(product).values() for product in products])


def get_all_products() -> None:
    """
    Get product data from all URLs and write to CSV files.
    """
    for url_key in URLS:
        products = get_page_with_products(URLS[url_key])
        write_to_csv(f"{url_key}.csv", products)


if __name__ == "__main__":
    get_all_products()
