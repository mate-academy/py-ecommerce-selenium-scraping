import csv
from dataclasses import dataclass, fields, astuple
from typing import Type
from urllib.parse import urljoin
from tqdm import tqdm

from selenium.common import (
    NoSuchElementException,
    ElementNotInteractableException,
)
from selenium.webdriver.common.by import By
from app.web_driver import WebDriverSingleton

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")
PHONE_URL = urljoin(HOME_URL, "phones/")
COMPUTER_URL = urljoin(HOME_URL, "computers/")
TABLET_URL = urljoin(COMPUTER_URL, "tablets")
LAPTOP_URL = urljoin(COMPUTER_URL, "laptops")
TOUCH_URL = urljoin(PHONE_URL, "touch")


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


PRODUCTS_FIELDS = [field.name for field in fields(Product)]


def parse_single_product(
    web_driver: Type[WebDriverSingleton], url: str
) -> list[Product]:
    with web_driver.get_instance() as driver:
        driver.get(url)

        # click button `accept cookies`
        accept_button = driver.find_element(By.CSS_SELECTOR, "a.acceptCookies")
        accept_button.click()

        # full page spread
        while True:
            try:
                pagination = driver.find_element(
                    By.CSS_SELECTOR, "a.ecomerce-items-scroll-more"
                )
                pagination.click()
            except NoSuchElementException as exc:
                print(
                    f"Something wrong with parse_single_product."
                    f"See the message below:\n {exc}"
                )
                break
            except ElementNotInteractableException as exc:
                print(
                    f"Something wrong with parse_single_product."
                    f"See the message below:\n {exc}"
                )
                break

        # find all products on page
        products = driver.find_elements(By.CLASS_NAME, "thumbnail")

        current_products = []

        for product in tqdm(products):
            curr_product = Product(
                title=product.find_element(
                    By.CLASS_NAME, "title"
                ).get_attribute("title"),
                description=product.find_element(
                    By.CLASS_NAME, "description"
                ).text,
                price=float(
                    product.find_element(By.CLASS_NAME, "price").text.replace(
                        "$", ""
                    )
                ),
                rating=len(
                    product.find_elements(By.CLASS_NAME, "glyphicon-star")
                ),
                num_of_reviews=int(
                    product.find_element(
                        By.CSS_SELECTOR, "p.pull-right"
                    ).text.split()[0]
                ),
            )
            current_products.append(curr_product)

        web_driver.close()

    return current_products


def write_products_to_csv(products: list[Product], filename: str) -> None:
    with open(filename, "w") as file:
        writer = csv.writer(file)
        writer.writerow(PRODUCTS_FIELDS)
        writer.writerows([astuple(product) for product in products])


def get_all_products() -> None:
    all_pages = [
        HOME_URL,
        PHONE_URL,
        COMPUTER_URL,
        TABLET_URL,
        LAPTOP_URL,
        TOUCH_URL,
    ]
    all_names_files = [
        "home.csv",
        "phones.csv",
        "computers.csv",
        "tablets.csv",
        "laptops.csv",
        "touch.csv",
    ]
    for page, filename in zip(all_pages, all_names_files):
        products = parse_single_product(WebDriverSingleton, page)
        write_products_to_csv(products, filename)


if __name__ == "__main__":
    get_all_products()
