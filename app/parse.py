import csv
import logging
import time
from dataclasses import dataclass
from urllib.parse import urljoin

from selenium.common import (
    NoSuchElementException,
    ElementClickInterceptedException,
    ElementNotInteractableException,
)
from selenium.webdriver import ActionChains
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement


BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")

logging.basicConfig(level=logging.INFO)

_driver: WebDriver | None = None


def set_driver(driver: WebDriver) -> None:
    global _driver
    _driver = driver


def get_driver() -> WebDriver:
    return _driver


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


def get_product(product_card: WebElement) -> Product:
    return Product(
        title=product_card.find_element(
            By.CLASS_NAME, "title"
        ).get_attribute("title"),
        description=product_card.find_element(
            By.CLASS_NAME, "description"
        ).text,
        price=float(
            product_card.find_element(
                By.CLASS_NAME, "price"
            ).text.replace("$", "")
        ),
        rating=len(
            product_card.find_elements(
                By.CLASS_NAME, "ws-icon-star"
            )
        ),
        num_of_reviews=int(
            product_card.find_element(
                By.CLASS_NAME, "review-count"
            ).text.split()[0]
        ),
    )


def get_all_products_from_dynamic_page(url: str) -> list[Product]:
    logging.info(f"Get all products from dynamic '{url}'")
    driver = get_driver()
    driver.get(urljoin(BASE_URL, url))

    try:
        close_button = driver.find_element(By.CLASS_NAME, "acceptCookies")
        driver.execute_script(
            "arguments[0].scrollIntoView(true);", close_button
        )
        close_button.click()
        logging.info("Closed cookie banner.")
    except NoSuchElementException:
        logging.info("No cookie banner found.")
    except ElementNotInteractableException:
        logging.info("Cookie banner was not interactable.")

    try:
        more = driver.find_element(By.CLASS_NAME, "ecomerce-items-scroll-more")
        while True:
            try:
                if not more.is_displayed():
                    break
                ActionChains(driver).move_to_element(more).click(
                    more
                ).perform()
                logging.info("Clicked 'Load More' button.")
                time.sleep(1)
                more = driver.find_element(
                    By.CLASS_NAME, "ecomerce-items-scroll-more"
                )
            except ElementClickInterceptedException:
                logging.warning(
                    "Load More button was blocked;"
                    " retrying after closing any obstructive elements."
                )
                cookie_button = driver.find_element(
                    By.CLASS_NAME, "acceptCookies"
                )
                if cookie_button:
                    cookie_button.click()
                time.sleep(1)
    except NoSuchElementException:
        logging.info("This page is static")

    cards = driver.find_elements(By.CLASS_NAME, "product-wrapper")

    return [get_product(card) for card in cards]


def get_all_products() -> None:
    driver = WebDriver()
    try:
        set_driver(driver)
        products = {
            "home.csv": get_all_products_from_dynamic_page(
                "/test-sites/e-commerce/more"
            ),
            "computers.csv": get_all_products_from_dynamic_page(
                "/test-sites/e-commerce/more/computers"
            ),
            "phones.csv": get_all_products_from_dynamic_page(
                "/test-sites/e-commerce/more/phones"
            ),
            "laptops.csv": get_all_products_from_dynamic_page(
                "/test-sites/e-commerce/more/computers/laptops"
            ),
            "tablets.csv": get_all_products_from_dynamic_page(
                "/test-sites/e-commerce/more/computers/tablets"
            ),
            "touch.csv": get_all_products_from_dynamic_page(
                "/test-sites/e-commerce/more/phones/touch"
            ),
        }
    finally:
        driver.quit()

    write_to_csv(products)


def write_to_csv(data: dict[str, list[Product]]) -> None:
    for output_file, products in data.items():
        logging.info(f"Writing products to {output_file} file")
        with open(output_file, "w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(
                ["title", "description", "price", "rating", "num_of_reviews"]
            )
            for product in products:
                writer.writerow(
                    [product.title, product.description, product.price,
                     product.rating, product.num_of_reviews]
                )


if __name__ == "__main__":
    get_all_products()
