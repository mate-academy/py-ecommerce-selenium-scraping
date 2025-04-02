import csv
import time
import os
from urllib.parse import urljoin

from bs4 import Tag
import requests
from bs4 import BeautifulSoup
from dataclasses import dataclass

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")


CSV_DIRECTORY = "tests"


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int
    additional_info: str


def parse_hdd_block_prices(product: Tag) -> str:
    hdd_buttons = product.select(".swatches .btn.swatch")
    return ", ".join(
        btn["value"] for btn in hdd_buttons
    ) if hdd_buttons else "N/A"



def parse_single_quote(product: Tag) -> Product:

    title = product.select_one(".card-title").text.strip()
    description = product.select_one(".card-text").text.strip()
    price = float(
        product.select_one(".float-end.pull-right").
        text.strip().replace("$", ""))

    num_of_reviews_text = product.select_one(".review-count").text.strip()
    num_of_reviews = int(
        num_of_reviews_text.split()[0]
    ) if num_of_reviews_text else 0

    rating = len(product.select(".ws-icon.ws-icon-star"))

    additional_info = parse_hdd_block_prices(product)

    return Product(title,
                   description,
                   price,
                   rating,
                   num_of_reviews,
                   additional_info)


def get_all_products(url: str = None) -> list[Product]:
    if url is None:
        pages = [
            urljoin(HOME_URL, "home"),
            urljoin(HOME_URL, "computers"),
            urljoin(HOME_URL, "laptops"),
            urljoin(HOME_URL, "tablets"),
            urljoin(HOME_URL, "phones"),
            urljoin(HOME_URL, "touch")
        ]
        urls_to_scrape = pages

    else:
        urls_to_scrape = [url]

    all_products = []

    for url in urls_to_scrape:
        products = []
        while True:
            response = requests.get(url)
            soup = BeautifulSoup(response.content, "html.parser")

            for product_block in soup.select(".product-wrapper.card-body"):
                products.append(parse_single_quote(product_block))

            load_more = soup.select_one(".btn.load-more")
            if load_more:
                next_url = urljoin(BASE_URL, load_more["href"])
                url = next_url
            else:
                break
        all_products.extend(products)

    return all_products


def save_products_to_csv(
        products: list[Product], output_csv_path: str) -> None:
    if not os.path.exists(CSV_DIRECTORY):
        os.makedirs(CSV_DIRECTORY)

    with open(
            os.path.join(CSV_DIRECTORY, output_csv_path
                         ), "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["title",
                         "description",
                         "price",
                         "rating",
                         "num_of_reviews",
                         "additional_info"])
        for product in products:
            writer.writerow([
                product.title,
                product.description,
                product.price,
                product.rating,
                product.num_of_reviews,
                product.additional_info
            ])


def main() -> None:
    pages = {
        "home.csv": urljoin(HOME_URL, "home"),
        "computers.csv": urljoin(HOME_URL, "computers"),
        "laptops.csv": urljoin(HOME_URL, "laptops"),
        "tablets.csv": urljoin(HOME_URL, "tablets"),
        "phones.csv": urljoin(HOME_URL, "phones"),
        "touch.csv": urljoin(HOME_URL, "touch"),
    }

    for filename, url in pages.items():
        products = get_all_products(url)
        save_products_to_csv(products, filename)


if __name__ == "__main__":
    main()
