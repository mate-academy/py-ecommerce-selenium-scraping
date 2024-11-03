import csv
from dataclasses import dataclass, astuple, fields
from types import TracebackType
from typing import Optional, Type

from selenium.webdriver.support import (
    expected_conditions as expected_conditions
)
from urllib.parse import urljoin

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.wait import WebDriverWait

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")
PAGES_TYPE = [
    "",
    "computers/",
    "computers/laptops/",
    "computers/tablets/",
    "phones/",
    "phones/touch/"
]


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


class ChromeDriver:
    def __init__(self) -> None:
        self._driver = webdriver.Chrome()

    def __enter__(self) -> webdriver.Chrome:
        return self._driver

    def __exit__(
            self,
            exc_type: Optional[Type[BaseException]],
            exc_val: Optional[BaseException],
            exc_tb: Optional[TracebackType]
    ) -> None:
        self._driver.close()


def get_catalog_name(url: str) -> str:
    return url.split("/")[-2] if url else "home"


def parse_single_product(product: WebElement) -> Product:
    return Product(
        title=product.find_element(
            By.CLASS_NAME, "title"
        ).get_attribute("title"),
        description=product.find_element(
            By.CLASS_NAME, "description"
        ).text,
        price=float(product.find_element(
            By.CLASS_NAME, "price"
        ).text.replace("$", "")),
        rating=len(product.find_elements(
            By.TAG_NAME, "span")
        ),
        num_of_reviews=int(product.find_element(
            By.CLASS_NAME, "review-count"
        ).text.split()[0]),
    )


def get_selenium_products_page(
        catalog: str,
        driver: webdriver.Chrome = None
) -> list[Product]:

    driver.get(HOME_URL + catalog)
    link_text = get_catalog_name(catalog).capitalize()
    button_link = driver.find_elements(By.LINK_TEXT, link_text)

    if button_link:
        button_link[0].click()

    try:
        cookie_close = (
            WebDriverWait(driver, 2)
            .until(
                expected_conditions.element_to_be_clickable(
                    (By.CSS_SELECTOR, "#closeCookieBanner")
                )
            )
        )
        cookie_close.click()
    except Exception:
        pass

    try:
        while True:
            more_button = (
                WebDriverWait(driver, 2)
                .until(
                    expected_conditions.element_to_be_clickable(
                        (By.CLASS_NAME, "ecomerce-items-scroll-more")
                    )
                )
            )
            more_button.click()
    except Exception:
        pass

    products = driver.find_elements(By.CLASS_NAME, "thumbnail")

    return [parse_single_product(product) for product in products]


def write_products_to_csv(catalog: str, products: list[Product]) -> None:
    name_to_write = get_catalog_name(catalog)
    with open(f"{name_to_write}.csv", "w+", newline="") as file:
        writer = csv.writer(file)
        writer.writerow([field.name for field in fields(Product)])
        writer.writerows([astuple(product) for product in products])


def get_all_products() -> None:
    with ChromeDriver() as driver:
        for catalog in PAGES_TYPE:
            products = get_selenium_products_page(catalog, driver)
            write_products_to_csv(catalog, products)


if __name__ == "__main__":
    get_all_products()
