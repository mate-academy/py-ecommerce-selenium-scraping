import csv
from dataclasses import dataclass
from urllib.parse import urljoin

from selenium import webdriver
from selenium.common import (
    NoSuchElementException,
    ElementNotInteractableException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

options = Options()
options.add_argument("--headless=new")  # Headless mode ON
driver = webdriver.Edge(options=options)

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


def bulk_product_create(entries: list[dict]) -> list[Product]:
    return [Product(**entry) for entry in entries]


def parse_category(category_url: str):
    driver.get(category_url)
    try:
        driver.find_element(By.CLASS_NAME, MORE_CLASS)
        while True:
            try:
                element = WebDriverWait(driver, 2).until(
                    EC.presence_of_element_located((By.CLASS_NAME, MORE_CLASS))
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
    entries = []
    for element in elements:
        entries.append(parse_element(element))
    return bulk_product_create(entries)


def parse_element(element) -> dict:
    return {
        "title": element.find_element(By.CLASS_NAME, "title").get_attribute("title"),
        "description": element.find_element(By.CLASS_NAME, "description").text,
        "price": float(
            element.find_element(By.CLASS_NAME, "price").text.replace("$", "")
        ),
        "rating": len(element.find_elements(By.CLASS_NAME, "ws-icon-star")),
        "num_of_reviews": element.find_element(
            By.CLASS_NAME, "review-count"
        ).text.split()[0],
    }


def parse_few_products():
    pass


def write_all_lists_to_csv(**kwargs) -> None:
    for item_name, items_list in kwargs.items():
        path = f"{item_name}.csv"
        write_product_list_to_csv(path, items_list)


def write_product_list_to_csv(path: str, products: list[Product]) -> None:
    with open(path, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(CSV_SCHEMA)
        for product in products:
            writer.writerow([getattr(product, column) for column in CSV_SCHEMA])


def get_all_products() -> None:
    write_all_lists_to_csv(
        home=parse_category(HOME_URL),
        computers=parse_category(COMPUTERS_URL),
        laptops=parse_category(LAPTOPS_URL),
        tablets=parse_category(TABLETS_URL),
        phones=parse_category(PHONES_URL),
        touch=parse_category(TOUCH_URL),
    )


if __name__ == "__main__":
    get_all_products()
