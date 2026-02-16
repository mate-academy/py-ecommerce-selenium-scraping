import csv
from dataclasses import dataclass, asdict
from urllib.parse import urljoin

from selenium import webdriver
from selenium.common import (
    NoSuchElementException,
    ElementClickInterceptedException,
    ElementNotInteractableException
)
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")
COMPUTER_PAGE_URL = urljoin(HOME_URL, "computers/")
LAPTOPS_URL = urljoin(COMPUTER_PAGE_URL, "laptops")
TABLETS_URL = urljoin(COMPUTER_PAGE_URL, "tablets")
PHONES_URL = urljoin(HOME_URL, "phones/")
TOUCH_URL = urljoin(PHONES_URL, "touch")

driver = webdriver.Chrome()


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


def all_more() -> None:
    while True:
        try:
            button = driver.find_element(
                By.CLASS_NAME, "ecomerce-items-scroll-more"
            )

            if not button.is_displayed():
                break

            button.click()

        except (
                NoSuchElementException,
                ElementClickInterceptedException,
                ElementNotInteractableException
        ):
            break


def parce_single_product(product: WebElement) -> Product:
    title = product.find_element(By.CLASS_NAME, "title").get_attribute("title")
    description = product.find_element(By.CLASS_NAME, "description").text
    price = float(product.find_element(By.CLASS_NAME, "price").text[1:])
    rating = len(product.find_elements(By.CLASS_NAME, "ws-icon-star"))
    num_of_reviews = int(
        product.find_element(
            By.CSS_SELECTOR, "span[itemprop='reviewCount']"
        ).text)
    return Product(title, description, price, rating, num_of_reviews)


def parce_single_page(url: str, filename: str) -> None:
    driver.get(url)

    try:
        accept_btn = driver.find_element(By.CLASS_NAME, "acceptCookies")
        accept_btn.click()
        print("accept cookies...")
    except (NoSuchElementException, ElementClickInterceptedException):
        pass

    all_more()

    products = driver.find_elements(By.CLASS_NAME, "product-wrapper")
    parsed_products = []
    for product in products:
        parsed_products.append(parce_single_product(product))

    with open(filename, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=parsed_products[0].__dataclass_fields__.keys()
        )
        writer.writeheader()
        writer.writerows(asdict(p) for p in parsed_products)


def get_all_products() -> None:
    parce_single_page(HOME_URL, "home.csv")
    parce_single_page(COMPUTER_PAGE_URL, "computers.csv")
    parce_single_page(LAPTOPS_URL, "laptops.csv")
    parce_single_page(TABLETS_URL, "tablets.csv")
    parce_single_page(PHONES_URL, "phones.csv")
    parce_single_page(TOUCH_URL, "touch.csv")


if __name__ == "__main__":
    get_all_products()
