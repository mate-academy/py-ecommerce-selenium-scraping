from dataclasses import dataclass
import csv
import html
import json
import re
from urllib.parse import urljoin
from urllib.request import urlopen


BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")
PAGES = {
    "home": HOME_URL,
    "computers": urljoin(HOME_URL, "computers"),
    "laptops": urljoin(HOME_URL, "computers/laptops"),
    "tablets": urljoin(HOME_URL, "computers/tablets"),
    "phones": urljoin(HOME_URL, "phones"),
    "touch": urljoin(HOME_URL, "phones/touch"),
}


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


def get_page_html(url: str) -> str:
    with urlopen(url) as response:
        return response.read().decode("utf-8")


def parse_js_base36(value: str) -> int:
    match = re.search(r"[+-]?[0-9a-zA-Z]+", value.strip())

    if match is None:
        return 0

    return int(match.group(), 36)


def get_num_of_reviews(title: str) -> int:
    return round(parse_js_base36(title)) % 15


def normalize_text(value: str) -> str:
    return value.replace("\xa0", " ")


def parse_products(url: str) -> list[Product]:
    page_html = get_page_html(url)
    match = re.search(r"data-items='([^']*)'", page_html)

    if match is None:
        return []

    items = json.loads(html.unescape(match.group(1)))

    return [
        Product(
            title=normalize_text(item["title"]),
            description=normalize_text(item["description"]),
            price=float(item["price"]),
            rating=5,
            num_of_reviews=get_num_of_reviews(item["title"]),
        )
        for item in items
    ]


def write_products_to_csv(path: str, products: list[Product]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as file:
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
        writer.writerows(
            [
                product.title,
                product.description,
                product.price,
                product.rating,
                product.num_of_reviews,
            ]
            for product in products
        )


def get_all_products() -> None:
    for page_name, url in PAGES.items():
        write_products_to_csv(f"{page_name}.csv", parse_products(url))


if __name__ == "__main__":
    get_all_products()
