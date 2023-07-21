import csv
from dataclasses import dataclass
from urllib.parse import urljoin
from unidecode import unidecode

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common import (
    ElementNotInteractableException,
    NoSuchElementException,
    ElementClickInterceptedException,
)
from selenium.webdriver.common.by import By

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")
COMPUTERS_URL = urljoin(HOME_URL, "computers/")
LAPTOPS_URL = urljoin(COMPUTERS_URL, "laptops")
TABLETS_URL = urljoin(COMPUTERS_URL, "tablets")
PHONES_URL = urljoin(HOME_URL, "phones/")
TOUCH_URL = urljoin(PHONES_URL, "touch")
LIST_URLS = [
    HOME_URL, COMPUTERS_URL, LAPTOPS_URL, TABLETS_URL, PHONES_URL, TOUCH_URL
]


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int

    @classmethod
    def parse_product(cls, product: BeautifulSoup) -> "Product":
        product = Product(
            title=product.select_one(".title")["title"],
            description=unidecode(product.select_one(".description").text),
            price=float(
                product.select_one(".pull-right").text.replace("$", "")
            ),
            rating=len(
                product.find_all("span", class_="glyphicon glyphicon-star")
            ),
            num_of_reviews=int(
                product.select_one(".ratings p").text.split()[0]
            ),
        )
        return product

    @classmethod
    def get_products_one_page(cls, url: str) -> list:
        with webdriver.Chrome() as driver:
            driver.get(url)
            accept_cookies = driver.find_element(
                By.CSS_SELECTOR, ".acceptCookies"
            )
            if accept_cookies:
                accept_cookies.click()

            try:
                while True:
                    button_more = driver.find_element(
                        By.CLASS_NAME, "ecomerce-items-scroll-more"
                    )
                    button_more.click()

            except (
                ElementNotInteractableException,
                NoSuchElementException,
                ElementClickInterceptedException,
            ):
                parsed_products = BeautifulSoup(
                    driver.page_source, "html.parser"
                ).select(".thumbnail")
                return [
                    cls.parse_product(product)
                    for product in parsed_products
                ]

    @classmethod
    def create_csv_file(cls, url: str, products: list) -> None:
        url = url.split("/")
        if url[-1] == "":
            name_file = url[-2]
            if name_file == "more":
                name_file = "home"
        else:
            name_file = url[-1]

        csv_path = name_file + ".csv"

        with open(csv_path, "w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(
                [
                    "title",
                    "description",
                    "price",
                    "rating",
                    "num_of_reviews",
                ]
            )
            for product in products:
                writer.writerow(
                    [
                        product.title,
                        product.description,
                        product.price,
                        product.rating,
                        product.num_of_reviews,
                    ]
                )


def get_all_products() -> None:
    for url in LIST_URLS:
        products = Product.get_products_one_page(url)
        Product.create_csv_file(url=url, products=products)


if __name__ == "__main__":
    get_all_products()
