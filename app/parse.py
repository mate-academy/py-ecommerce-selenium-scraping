import csv
from dataclasses import dataclass, astuple, fields
from urllib.parse import urljoin

from bs4 import BeautifulSoup, Tag
from selenium import webdriver
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from typing import Optional


BASE_URL = "https://webscraper.io/"

URLS = {
    "home.csv": urljoin(BASE_URL, "test-sites/e-commerce/more/"),
    "computers.csv": urljoin(
        BASE_URL, "test-sites/e-commerce/more/computers/"
    ),
    "laptops.csv": urljoin(
        BASE_URL, "test-sites/e-commerce/more/computers/laptops"
    ),
    "tablets.csv": urljoin(
        BASE_URL, "test-sites/e-commerce/more/computers/tablets"
    ),
    "phones.csv": urljoin(BASE_URL, "test-sites/e-commerce/more/phones/"),
    "touch.csv": urljoin(BASE_URL, "test-sites/e-commerce/more/phones/touch")
}


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int

    @staticmethod
    def parse_single_product(product_soup: Tag) -> "Product":
        return Product(
            title=product_soup.select_one(".title")["title"],
            description=product_soup.select_one("p.description").text.replace(
                "\xa0", " "
            ),
            price=float(product_soup.select_one(".price").text[1:]),
            rating=len(product_soup.select("span.ws-icon-star")),
            num_of_reviews=int(
                product_soup.select_one(".review-count").text.split()[0]
            ),
        )


PRODUCT_FIELDS = [field.name for field in fields(Product)]

_driver: WebDriver | None = None


def parse_single_product(product_soup: Tag) -> Product:
    return Product(
        title=product_soup.select_one(".title")["title"],
        description=product_soup.select_one("p.description").text.replace(
            "\xa0", " "
        ),
        price=float(product_soup.select_one(".price").text[1:]),
        rating=len(product_soup.select("span.ws-icon-star")),
        num_of_reviews=int(
            product_soup.select_one(".review-count").text.split()[0]
        ),
    )


def parse_page(url: str) -> [Product]:
    driver = _driver
    driver.get(url)
    try:
        more_button = driver.find_element(By.CLASS_NAME, "btn")
    except Exception:
        more_button = None
    if more_button:
        while not more_button.get_property("style"):
            driver.execute_script("arguments[0].click();", more_button)

    soup = BeautifulSoup(driver.page_source, "html.parser")

    product_cards = soup.select(".thumbnail")
    products = [Product.parse_single_product(product) for product in product_cards]

    return products


def write_products_to_csv(products: [Product], file_name: str) -> None:
    with open(file_name, "w") as file:
        writer = csv.writer(file)
        writer.writerow(PRODUCT_FIELDS)
        writer.writerows([astuple(product) for product in products])


def get_all_products() -> None:
    with webdriver.Chrome() as new_driver:
        global _driver
        _driver = new_driver
        for file_name, url in URLS.items():
            products = parse_page(url=url)
            write_products_to_csv(products=products, file_name=file_name)


if __name__ == "__main__":
    get_all_products()
