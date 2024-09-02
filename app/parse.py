import csv
from dataclasses import dataclass, fields
from typing import List
from urllib.parse import urljoin

from selenium import webdriver
from selenium.common import (
    NoSuchElementException,
    ElementClickInterceptedException,
    ElementNotInteractableException,
    TimeoutException,
)
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec


BASE_URL = "https://webscraper.io/"


URLS_TO_PARSE = {
    "home": "test-sites/e-commerce/more/",
    "laptops": "test-sites/e-commerce/more/computers/laptops",
    "tablets": "test-sites/e-commerce/more/computers/tablets",
    "phones": "test-sites/e-commerce/more/phones",
    "touch": "test-sites/e-commerce/more/phones/touch",
    "computers": "test-sites/e-commerce/more/computers",
}


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


PRODUCT_FIELDS = [field.name for field in fields(Product)]


class Emulator:
    _driver: WebDriver | None = None

    @staticmethod
    def get_chrome_driver_options() -> Options:
        options = Options()
        options.add_argument("--headless")
        return options

    @staticmethod
    def set_driver() -> WebDriver:
        driver = webdriver.Chrome(options=Emulator.get_chrome_driver_options())
        Emulator._driver = driver
        return driver

    @staticmethod
    def get_driver() -> WebDriver:
        return Emulator._driver

    @staticmethod
    def accept_cookie_banner_if_present() -> None:
        try:
            driver = Emulator._driver
            cookie_banner = driver.find_element(By.ID, "cookieBanner")
            accept_button = cookie_banner.find_element(
                By.CSS_SELECTOR, ".acceptContainer > button.acceptCookies"
            )
            accept_button.click()
        except NoSuchElementException:
            pass

    @staticmethod
    def exit_driver() -> None:
        Emulator.get_driver().quit()


def parse_single_product(product_soup: WebElement) -> Product:
    return Product(
        title=product_soup.find_element(
            By.CSS_SELECTOR, ".title"
        ).get_attribute("title"),
        description=product_soup.find_element(
            By.CSS_SELECTOR, ".description"
        ).text,
        price=float(
            product_soup.find_element(By.CSS_SELECTOR, ".price").text.replace(
                "$", ""
            )
        ),
        rating=len(
            product_soup.find_elements(
                By.CSS_SELECTOR, ".ratings span.ws-icon-star"
            )
        ),
        num_of_reviews=int(
            product_soup.find_element(
                By.CSS_SELECTOR, ".ratings > p.review-count"
            ).text.split()[0]
        ),
    )


def parse_product_page(url: str) -> [Product]:
    driver = Emulator.get_driver()
    driver.get(urljoin(BASE_URL, url))
    Emulator.accept_cookie_banner_if_present()

    while True:
        try:
            more_button = driver.find_element(
                By.CSS_SELECTOR, "a.ecomerce-items-scroll-more"
            )
        except NoSuchElementException:
            break

        try:
            wait = WebDriverWait(driver, 1)
            more_button = wait.until(ec.element_to_be_clickable(more_button))
            more_button.click()
        except (
            ElementClickInterceptedException,
            ElementNotInteractableException,
            TimeoutException,
        ):
            break

    products = driver.find_elements(By.CSS_SELECTOR, ".product-wrapper")
    return [parse_single_product(product) for product in products]


def write_products_to_csv(products: List[Product], file_to_write: str) -> None:
    with open(file_to_write, "w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(PRODUCT_FIELDS)
        for product in products:
            writer.writerow(
                [
                    product.title,
                    product.description,
                    product.price,
                    product.rating,
                    product.num_of_reviews,
                ]
            )


def get_all_products() -> None:
    Emulator.set_driver()

    for file, url in URLS_TO_PARSE.items():
        products = parse_product_page(url)
        write_products_to_csv(products, file + ".csv")

    Emulator.exit_driver()


if __name__ == "__main__":
    get_all_products()
