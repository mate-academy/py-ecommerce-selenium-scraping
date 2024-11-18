import csv
from dataclasses import dataclass, fields
from urllib.parse import urljoin

import requests
from bs4 import Tag, BeautifulSoup

from selenium_dependency import get_dynamic_content

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")
PAGES_FILES = {
    "home.csv": HOME_URL,  # random
    "computers.csv": urljoin(HOME_URL, "computers"),
    "laptops.csv": urljoin(HOME_URL, "computers/laptops"),
    "tablets.csv": urljoin(HOME_URL, "computers/tablets"),
    "phones.csv": urljoin(HOME_URL, "phones/"),
    "touch.csv": urljoin(HOME_URL, "phones/touch"),
}


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


PRODUCT_FIELDS = [field.name for field in fields(Product)]


def parse_single_product(product: Tag) -> Product:
    product = Product(
        title=product.select_one(".title")["title"],
        description=product.select_one(".description").text.replace("\xa0", " "),
        price=float(product.select_one(".price").text.replace("$", "")),
        rating=len(product.select(".ws-icon-star")),
        num_of_reviews=int(product.select_one(".review-count").text.split()[0]),
    )
    return product


def get_products_from_page(url: str) -> list[Product]:
    print(f"getting products from {url} via get products from page")
    response = requests.get(url)
    print(f"Status code {response.status_code}")
    soup = BeautifulSoup(response.text, "html.parser")
    products = soup.find_all("div", {"class": "card-body"})

    if not products:
        print(f"No products found via static scraping. "
              f"Trying dynamic scraping for {url}")
        dynamic_html = get_dynamic_content(url)
        soup = BeautifulSoup(dynamic_html, "html.parser")
        products = soup.find_all("div", {"class": "card-body"})

    if not products:
        print(f"No products found by url {url}")
        return []
    else:
        return [parse_single_product(product) for product in products]


def write_products_to_csv(products: list[Product], file_name: str) -> None:
    with open(file_name, "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(PRODUCT_FIELDS)
        for product in products:
            writer.writerow([
                product.title,
                product.description,
                product.price,
                product.rating,
                product.num_of_reviews,
            ])


def get_all_products() -> None:
    for file_name, url in PAGES_FILES.items():
        print(f"working on {file_name}, url {url}")
        write_products_to_csv(
            get_products_from_page(url),
            file_name
        )


if __name__ == "__main__":
    get_all_products()
