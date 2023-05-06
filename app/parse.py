import csv
from dataclasses import dataclass
from typing import List

from selenium import webdriver
from selenium.common.exceptions import (
    NoSuchElementException,
    ElementNotInteractableException,
)
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from urllib.parse import urljoin

BASE_URL = "https://webscraper.io/"
URLS = [
    "test-sites/e-commerce/more/",
    "test-sites/e-commerce/more/computers",
    "test-sites/e-commerce/more/computers/laptops",
    "test-sites/e-commerce/more/computers/tablets",
    "test-sites/e-commerce/more/phones",
    "test-sites/e-commerce/more/phones/touch"
]


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


def product_to_tuple(product: Product) -> tuple:
    return tuple(product.__dict__.values())


def write_to_csv(output_csv_path: str, products: List[Product]) -> None:
    field_names = Product.__dataclass_fields__.keys()
    with open(output_csv_path, "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(field_names)
        writer.writerows([product_to_tuple(product) for product in products])


def configure_driver() -> webdriver:
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    return webdriver.Chrome(options=chrome_options)


def accept_cookies_and_scroll(driver: webdriver) -> None:
    try:
        driver.find_element(By.CLASS_NAME, "acceptCookies").click()
    except (
            NoSuchElementException

    ):
        pass
    while True:
        try:
            driver.find_element(
                By.CSS_SELECTOR, "a.ecomerce-items-scroll-more"
            ).click()
        except (NoSuchElementException, ElementNotInteractableException):

            break


def parse_single_product(product: dict) -> Product:
    return Product(
        title=product["title"],
        description=product["description"],
        price=float(product["price"]),
        rating=int(product["rating"]),
        num_of_reviews=int(product["num_of_reviews"])
    )


def get_parsed_products(driver: webdriver) -> List[Product]:
    accept_cookies_and_scroll(driver)
    products_drivers = driver.find_elements(By.CLASS_NAME, "thumbnail")
    products_instances = []
    for product in products_drivers:
        products_instances.append(parse_single_product({
            "title": product.find_element(
                By.CLASS_NAME, "title"
            ).get_attribute("title"),
            "description": product.find_element(
                By.CLASS_NAME, "description"
            ).text,
            "price": product.find_element(
                By.CLASS_NAME, "price"
            ).text.replace("$", ""),
            "rating": len(product.find_elements(
                By.CSS_SELECTOR, "div.ratings span.glyphicon-star"
            )),
            "num_of_reviews": product.find_element(
                By.CLASS_NAME, "ratings"
            ).text.replace(" reviews", "")
        }))
    return products_instances


def get_all_products() -> None:
    driver = configure_driver()
    for url in URLS:
        driver.get(urljoin(BASE_URL, url))
        correct_products = get_parsed_products(driver)
        write_to_csv(
            f"{url.split('/')[-1] if url.split('/')[-1] else 'home'}.csv",
            correct_products
        )
    driver.quit()


if __name__ == "__main__":
    get_all_products()
