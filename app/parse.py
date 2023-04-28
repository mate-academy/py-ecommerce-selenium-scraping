import csv
from dataclasses import dataclass, astuple, fields
from urllib.parse import urljoin
import requests

from selenium import webdriver
from selenium.webdriver.common.by import By

from bs4 import BeautifulSoup

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")

PRODUCT_OUTPUT_CSV_PATH = "products.csv"


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int
    additional_info: dict


PRODUCT_FIELDS = [field.name for field in fields(Product)]

def parse_single_product(product_soup: BeautifulSoup) -> Product:

    return Product(
        title=product_soup.select_one(".title")["title"],
        description=product_soup.select_one(".description").text,
        price=float(product_soup.select_one(".price").text.replace("$", "")),
        rating=len(product_soup.select(".glyphicon-star")),
        num_of_reviews=int(
            product_soup.select_one(".ratings > p.pull-right").text.split()[0]
        ),
    )


def get_num_pages(page_soup:BeautifulSoup) -> int:
    pagination = page_soup.select_one(".pagination")

    if pagination in None:
        return 1

    return int(pagination.select("li")[-2].text)


def get_single_page_products(page_soup: BeautifulSoup) -> [Product]:
    products = page_soup.select(".thumbnail")

    return [parse_single_product(product_soup) for product_soup in products]


def get_all_products() -> None:
    page = requests.get(HOME_URL).content
    home_page_soup = BeautifulSoup(page, "html.parser")

    num_pages = get_num_pages(home_page_soup)

    all_products = get_single_page_products(home_page_soup)

    for page_num in range(2, num_pages + 1):
        page = requests.get(HOME_URL, {"page": page_num}).content
        soup = BeautifulSoup(page, "html.parser")
        all_products.extend(get_single_page_products(soup))

    return all_products


def write_product_to_csv(products: [Product]) -> None:
    with open(PRODUCT_OUTPUT_CSV_PATH, "w") as file:
        writer = csv.writer(file)
        writer.writerow(PRODUCT_FIELDS)
        writer.writerows(astuple(product) for product in products)


if __name__ == "__main__":
    get_all_products()

