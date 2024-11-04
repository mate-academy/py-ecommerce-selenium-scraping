import datetime
import csv
from dataclasses import dataclass
from urllib.parse import urljoin

from selenium import webdriver
from selenium.common import (
    NoSuchElementException,
    ElementNotInteractableException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.wait import WebDriverWait


driver = webdriver.Chrome()

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")
PRODUCT_URL = urljoin(HOME_URL, "product/")

COMPUTERS_URL = urljoin(HOME_URL, "computers")
LAPTOPS_URL = COMPUTERS_URL + "/laptops"
TABLETS_URL = COMPUTERS_URL + "/tablets"
PHONES_URL = urljoin(HOME_URL, "phones")
TOUCH_URL = PHONES_URL + "/touch"

MORE_CLASS = "ecomerce-items-scroll-more"

CSV_SCHEMA = ["title", "description", "price", "rating", "num_of_reviews"]


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


def parse_category(category_url: str) -> list[Product]:
    driver.get(category_url)
    products = []
    try:
        while True:
            try:
                element = WebDriverWait(driver, 2).until(
                    ec.presence_of_element_located((By.CLASS_NAME, MORE_CLASS))
                )
                if element.is_displayed() and element.is_enabled():
                    element.click()
                else:
                    break
            except (NoSuchElementException, ElementNotInteractableException):
                break
    except:
        pass

    elements = driver.find_elements(By.CLASS_NAME, "card-body")
    for element in elements:
        products.append(
            Product(
                title=element.find_element(
                    By.CLASS_NAME, "title"
                ).get_attribute(
                    "title"
                ),
                description=element.find_element(
                    By.CLASS_NAME, "description"
                ).text,
                price=float(
                    element.find_element
                    (By.CLASS_NAME, "price"
                     ).text.replace("$", "")
                ),
                rating=len(
                    element.find_elements(
                        By.CLASS_NAME, "ws-icon-star")
                ),
                num_of_reviews=int(
                    element.find_element(
                        By.CLASS_NAME, "review-count"
                    ).text.split()[0]
                ),
            )
        )

    return products


def write_to_csv(**kwargs) -> None:
    for item_name, items_list in kwargs.items():
        path = f"{item_name}.csv"
        with open(path, mode="w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(CSV_SCHEMA)
            for product in items_list:

                writer.writerow(
                    [getattr(product, column) for column in CSV_SCHEMA]
                )


if __name__ == "__main__":
    start = datetime.datetime.now()
    write_to_csv(
        home=parse_category(HOME_URL),
        computers=parse_category(COMPUTERS_URL),
        laptops=parse_category(LAPTOPS_URL),
        tablets=parse_category(TABLETS_URL),
        phones=parse_category(PHONES_URL),
        touch=parse_category(TOUCH_URL),
    )
    end = datetime.datetime.now()
    print(end - start)
