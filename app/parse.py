import csv
from dataclasses import dataclass
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


def get_links(soup: BeautifulSoup) -> list[str]:
    links = soup.select(".category-link ")
    return [link.get("href") for link in links]


def create_product(product: BeautifulSoup) -> Product:
    title = product.select_one(".title").get("title")
    description = product.select_one(".description").text
    price = float(product.select_one(".price").text.replace("$", ""))
    rating = int(product.select_one("div.ratings > p.pull-right").text.split()[0])
    num_of_reviews = int(product.select_one("div.ratings > p[data-rating]").get("data-rating"))
    return Product(title=title, description=description, price=price, rating=rating, num_of_reviews=num_of_reviews)


def parse_page(soup: BeautifulSoup, tag: str, selector_type: str, selector_name: str):
    products = soup.find_all(tag, {selector_type: selector_name})
    return [create_product(product) for product in products]


def write_to_csv(products: list, filename: str):
    with open(filename, mode="w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["Title", "Description", "Price", "Rating", "Number of Reviews"])
        for product in products:
            writer.writerow([product.title, product.description, product.price, product.rating, product.num_of_reviews])


def get_all_products() -> None:
    response = requests.get(HOME_URL)
    soup = BeautifulSoup(response.content, "html.parser")
    products = parse_page(soup=soup, tag="div", selector_type="class", selector_name="thumbnail")
    write_to_csv(products, "home.csv")


if __name__ == "__main__":
    get_all_products()
