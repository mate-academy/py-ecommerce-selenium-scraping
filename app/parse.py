import csv
from dataclasses import dataclass, fields, astuple
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import (
    NoSuchElementException,
    ElementClickInterceptedException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more")
COMPUTERS_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/computers")
LAPTOPS_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/computers/laptops")
TABLETS_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/computers/tablets")
PHONES_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/phones")
TOUCH_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/phones/touch")

URLS_FIELDS = [
    HOME_URL,
    COMPUTERS_URL,
    LAPTOPS_URL,
    TABLETS_URL,
    PHONES_URL,
    TOUCH_URL
]


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


def parse_single_product(product_soup: BeautifulSoup) -> Product:
    return Product(
        title=product_soup.select_one(".title")["title"],
        description=product_soup.select_one(".description").text,
        price=float(product_soup.select_one(".price").text.replace("$", "")),
        rating=str(product_soup.select_one(".ratings")).count("ws-icon-star"),
        num_of_reviews=int(product_soup.select_one(".review-count").text[0]),
    )


def get_all_products(url: str, driver: WebDriver) -> list[Product]:
    driver.get(url)

    while True:
        try:
            more_button = driver.find_element(
                By.CLASS_NAME, "ecomerce-items-scroll-more"
            )
            more_button.click()
        except (NoSuchElementException, ElementClickInterceptedException):
            break

    products = BeautifulSoup(
        driver.page_source,
        "html.parser").select(".thumbnail")

    return [parse_single_product(product_soup) for product_soup in products]


def write_quotes_to_csv(products: [Product], filename: str) -> None:
    with open(filename, "w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(PRODUCT_FIELDS)
        writer.writerows([astuple(product) for product in products])


def parse_urls(driver: WebDriver, urls: list) -> list[Product]:
    all_products = []
    for url in urls:
        all_products.extend(get_all_products(url, driver))
    return all_products


def main(output_csv_path: str) -> None:
    with webdriver.Chrome() as new_driver:
        set_driver(new_driver)
        products = parse_urls(driver=new_driver, urls=URLS_FIELDS)
        write_quotes_to_csv(products, output_csv_path)


if __name__ == "__main__":
    main("info.csv")
