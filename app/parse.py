import csv
import logging
import sys
from dataclasses import dataclass, fields, asdict
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup, Tag

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("parser.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


def save_data_to_csv(name: str, products: list[Product]) -> None:
    with open(f"{name}.csv", mode="w", newline="", encoding="utf-8") as csvfile:
        fieldnames = [field.name for field in fields(Product)]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        if products is None:
            return
        for product in products:
            writer.writerow(asdict(product))  # Serialize and write


def make_safe_request(url: str) -> str:
    try:
        response = requests.get(url=url)
        if response.status_code == 200:
            return response.text
    except Exception as e:
        logging.warning(e)


def get_soup_from_page(url: str) -> BeautifulSoup | None:
    soup = BeautifulSoup(make_safe_request(url), "html.parser")
    if soup.body and "No products found!" in soup.get_text():
        return None
    return soup


def get_product_price(product: Tag) -> float:
    price_container = product.select_one(".price")
    price = price_container.select_one("[itemprop='price']").text.strip().replace("$", "")
    return float(price)


def get_product_ratings(product: Tag) -> dict:
    ratings_container = product.select_one(".ratings")
    rating_tag = ratings_container.select_one("p[data-rating]")
    num_of_reviews = ratings_container.select_one("[itemprop='reviewCount']").text.strip()

    return {"rating": int(rating_tag["data-rating"]), "num_of_reviews": int(num_of_reviews)}


def get_product_title(product):
    title_container = product.select_one(".title")
    return title_container["title"]


def get_products_from_single_page(soup: BeautifulSoup) -> list[Product] | None:
    products = []
    for product in soup.select(".card-body"):
        products.append(Product(
            title=get_product_title(product=product),
            description=product.select_one(".description ").text,
            price=get_product_price(product=product),
            rating=get_product_ratings(product=product)["rating"],
            num_of_reviews=get_product_ratings(product=product)["num_of_reviews"]
        ))
    return products


def get_products_from_page(home_url: str, path: str = None):
    url = urljoin(home_url, path)
    logging.info(f"Working on {url}")
    soup = get_soup_from_page(url=url)

    products = get_products_from_single_page(soup=soup)

    name_of_csv_file = "home"
    if path:
        name_of_csv_file = path.split("/")[-1]
    save_data_to_csv(name=name_of_csv_file, products=products)


def get_all_products() -> None:
    get_products_from_page(home_url=HOME_URL)
    get_products_from_page(home_url=HOME_URL, path="computers")


if __name__ == "__main__":
    get_all_products()
