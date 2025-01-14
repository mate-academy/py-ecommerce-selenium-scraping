import time
import csv
from typing import List

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.ie.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import (
    NoSuchElementException,
    ElementNotInteractableException,
    StaleElementReferenceException,
    WebDriverException,
)
from dataclasses import dataclass, fields, astuple
from urllib.parse import urljoin


BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")
COMPUTERS_URL = urljoin(HOME_URL, "computers/")
PHONES_URL = urljoin(HOME_URL, "phones/")
LAPTOPS_URL = urljoin(COMPUTERS_URL, "laptops")
TABLETS_URL = urljoin(COMPUTERS_URL, "tablets")
TOUCH_URL = urljoin(PHONES_URL, "touch")

COLUMN_NAMES = {
    "title": "title",
    "description": "description",
    "price": "price",
    "rating": "rating",
    "num_of_reviews": "num_of_reviews"
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
    try:
        title = product.find_element(By.CLASS_NAME, "title").get_property("title")
        description = product.find_element(By.CLASS_NAME, "description").text
        price = float(product.find_element(By.CLASS_NAME, "price").text.replace("$", ""))
        rating = len(product.find_elements(By.CLASS_NAME, "ws-icon-star"))
        num_of_reviews = int(product.find_element(By.CLASS_NAME, "review-count").text.split()[0])
        return Product(title, description, price, rating, num_of_reviews)
    except NoSuchElementException as e:
        raise ValueError(f"Не вдалося спарсити продукт: {e}")


def scroll_page(driver: WebDriver) -> None:
    while True:
        try:
            button = driver.find_element(
                By.CLASS_NAME,
                "ecomerce-items-scroll-more"
            )
            driver.execute_script(
                "arguments[0].scrollIntoView(true);",
                button
            )
            button.click()
            time.sleep(1)
        except (NoSuchElementException, ElementNotInteractableException):
            break
        except (StaleElementReferenceException, WebDriverException):
            break


def get_products(url: str, with_scroll: bool = False) -> List[Product]:
    try:
        with webdriver.Chrome() as driver:
            driver.get(url)
            if with_scroll:
                scroll_page(driver)
            products = [
                parse_single_product(product)
                for product in driver.find_elements(By.CLASS_NAME, "card-body")
            ]
        return products
    except NoSuchElementException as e:
        raise RuntimeError(f"Елемент не знайдено на сторінці {url}: {e}")
    except WebDriverException as e:
        raise RuntimeError(f"Помилка WebDriver при отриманні продуктів із {url}: {e}")


def save_to_file(filename: str, products: List[Product]) -> None:
    with open(filename, "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow([COLUMN_NAMES[field] for field in PRODUCT_FIELDS])
        writer.writerows([astuple(product) for product in products])


def get_all_products() -> None:
    datasets = {
        "laptops.csv": (LAPTOPS_URL, True),
        "tablets.csv": (TABLETS_URL, True),
        "home.csv": (HOME_URL, False),
        "computers.csv": (COMPUTERS_URL, False),
        "phones.csv": (PHONES_URL, False),
        "touch.csv": (TOUCH_URL, True),
    }

    for filename, (url, with_scroll) in datasets.items():
        products = get_products(url, with_scroll)
        save_to_file(filename, products)



if __name__ == "__main__":
    get_all_products()
