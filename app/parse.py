import csv
from dataclasses import dataclass, fields, astuple
from urllib.parse import urljoin

from selenium import webdriver
from selenium.common import (
    ElementClickInterceptedException,
    ElementNotInteractableException,
    NoSuchElementException,
    TimeoutException,
)
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait
from tqdm import tqdm

BASE_URL = "https://webscraper.io/test-sites/e-commerce/more/"
PAGES = {
    "home": "",
    "computers": "computers",
    "laptops": "computers/laptops",
    "tablets": "computers/tablets",
    "phones": "phones",
    "touch": "phones/touch",
}


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


PRODUCT_FIELDS = [field.name for field in fields(Product)]


def initialize_driver() -> WebDriver:
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--headless")
    driver = webdriver.Chrome(options=chrome_options)

    return driver


def accept_cookies(driver: WebDriver) -> None:
    while True:
        try:
            button = (
                driver.find_element(By.CLASS_NAME, "acceptCookies")
            )
            button.click()
        except (
            ElementClickInterceptedException,
            ElementNotInteractableException,
            NoSuchElementException,
            TimeoutException,
        ):
            break


def show_more_products(driver: WebDriver) -> None:
    while True:
        try:
            button = WebDriverWait(driver, 10).until(
                expected_conditions.element_to_be_clickable(
                    (By.CLASS_NAME, "ecomerce-items-scroll-more")
                )
            )
            button.click()
        except (
                ElementClickInterceptedException,
                ElementNotInteractableException,
                NoSuchElementException,
                TimeoutException,
        ):
            break


def parse_single_product(card: WebElement) -> Product:
    title = card.find_element(By.CLASS_NAME, "title").get_attribute("title")
    description = card.find_element(By.CLASS_NAME, "description").text
    price = float(
        card.find_element(By.CLASS_NAME, "price").text.replace("$", "")
    )
    rating = len(card.find_elements(By.CLASS_NAME, "ws-icon-star"))
    num_of_reviews = int(
        card.find_element(By.CLASS_NAME, "review-count").text.split()[0]
    )

    return Product(
        title=title,
        description=description,
        price=price,
        rating=rating,
        num_of_reviews=num_of_reviews,
    )


def write_products_to_csv(
    products: list[Product],
    path: str,
) -> None:
    with open(path, "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(PRODUCT_FIELDS)
        writer.writerows([astuple(product) for product in products])


def get_all_products() -> None:
    driver = initialize_driver()

    try:
        for name, link in PAGES.items():
            driver.get(urljoin(BASE_URL, link))
            accept_cookies(driver)
            show_more_products(driver)
            cards = driver.find_elements(By.CLASS_NAME, "card-body")
            products = [parse_single_product(card) for card in tqdm(cards)]
            write_products_to_csv(products, f"{name}.csv")

    finally:
        driver.close()


if __name__ == "__main__":
    get_all_products()
