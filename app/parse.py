import csv
import time
from dataclasses import dataclass
from urllib.parse import urljoin

from selenium.common import NoSuchElementException, ElementNotInteractableException, TimeoutException
from selenium.webdriver.common.by import By
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")
COMPUTERS_URL = urljoin(HOME_URL, "computers")
PHONES_URL = urljoin(HOME_URL, "phones")
LAPTOPS_URL = urljoin(HOME_URL, "computers/laptops")
TABLETS_URL = urljoin(HOME_URL, "computers/tablets")
TOUCH_URL = urljoin(HOME_URL, "phones/touch")


CSV_SCHEMA = ["title", "description", "price", "rating", "num_of_reviews"]


options = Options()
options.headless = True

driver = webdriver.Firefox(options=options)


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


def create_products(products_data: list[dict]) -> [Product]:
    return [Product(**element) for element in products_data]


def parse_element(element: WebElement) -> dict:
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


def parse_category(category_url: str) -> None:
    driver.get(category_url)
    while True:
        try:
            load_more_button = WebDriverWait(driver, 10).until(
                expected_conditions.presence_of_element_located((By.CLASS_NAME, "ecomerce-items-scroll-more"))
            )
            if load_more_button.is_displayed() and load_more_button.is_enabled():
                load_more_button.click()
                time.sleep(2)
            else:
                break
        except (NoSuchElementException, ElementNotInteractableException, TimeoutException):
            print(f"Unable to find 'Load More' button or it's not interactable. Exiting...")
            break

    elements = driver.find_elements(By.CLASS_NAME, "thumbnail")
    category_data = []
    for element in elements:
        category_data.append(parse_element(element))
    return create_products(category_data)


def parse_list_of_categories(list_categories: list[str]):
    list_products = []

    for category in list_categories:
        list_products.append(parse_category(category))

    return list_products


def write_to_csv(path: str, products: list[Product]) -> None:
    with open(path, mode="w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(CSV_SCHEMA)
        for product in products:
            writer.writerow(
                [getattr(product, column) for column in CSV_SCHEMA]
            )


def write_all_lists_to_csv(**kwargs) -> None:
    for item_name, items_list in kwargs.items():
        path = f"{item_name}.csv"
        write_to_csv(path, items_list)


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
