import csv
import time
from dataclasses import dataclass
from typing import Any
from urllib.parse import urljoin

from selenium import webdriver
from selenium.common import (
    NoSuchElementException,
    ElementNotInteractableException,
    ElementClickInterceptedException
)
from selenium.webdriver.common.by import By

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int

    @classmethod
    def class_keys(cls) -> Any:
        return cls.__annotations__.keys()

    @classmethod
    def save_to_csv(cls, file_path: str, products: list["Product"]) -> None:
        with open(file_path, "w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(cls.class_keys())
            for product in products:
                row = [getattr(product, key) for key in cls.class_keys()]
                writer.writerow(row)


def get_driver(headless: bool = False) -> webdriver:
    options = webdriver.ChromeOptions()
    if headless:
        options.add_argument("--headless")
    return webdriver.Chrome(options=options)


def get_products_from_page(driver: webdriver) -> list[Product]:
    cards = driver.find_elements(By.CLASS_NAME, "thumbnail")
    products = [get_product(card) for card in cards]
    return products


def get_product(card: webdriver) -> Product:
    """Get product information from a card element."""
    title = card.find_element(By.CLASS_NAME, "title")
    description = card.find_element(By.CLASS_NAME, "description")
    price = card.find_element(By.CLASS_NAME, "price")
    rating_wrapper = card.find_element(By.CLASS_NAME, "ratings")
    reviews = rating_wrapper.find_element(By.CLASS_NAME, "pull-right")
    reviews = int(reviews.text.split()[0])
    stars = rating_wrapper.find_elements(By.CLASS_NAME, "glyphicon-star")
    return Product(
        title=title.text,
        description=description.text,
        price=float(price.text.replace("$", "")),
        rating=len(stars),
        num_of_reviews=reviews,
    )


def get_products_by_category(driver: webdriver, category: str) -> None:
    """Get all products from a category."""

    driver.find_element(By.LINK_TEXT, category).click()
    try:
        driver.find_element(By.ID, "closeCookieBanner").click()
    except (NoSuchElementException, ElementNotInteractableException):
        pass

    while True:
        try:
            time.sleep(0.1)
            driver.find_element(By.LINK_TEXT, "More").click()
        except (
                NoSuchElementException,
                ElementNotInteractableException,
                ElementClickInterceptedException
        ):
            break
    driver.execute_script("window.scrollTo(0, 0);")
    products = get_products_from_page(driver)
    Product.save_to_csv(f"{category.lower()}.csv", products)


def get_all_products() -> None:
    """Get all products from the home page."""
    driver = get_driver()
    driver.maximize_window()
    driver.get(HOME_URL)

    products = get_products_from_page(driver)
    Product.save_to_csv("home.csv", products)

    categories = ("Computers", "Tablets", "Laptops", "Phones", "Touch")

    for category in categories:
        get_products_by_category(driver, category)
    driver.quit()


if __name__ == "__main__":
    get_all_products()
