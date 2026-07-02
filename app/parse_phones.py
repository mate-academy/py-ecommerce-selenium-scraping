import requests
from bs4 import BeautifulSoup, Tag

from app.constants import PHONES_URL
from app.models import Product


def parse_single_phones_product(product: Tag) -> Product:
    return Product(
        title=product.select_one(".title")["title"],
        description=product.select_one(".description").text,
        price=float(product.select_one(".price").text.replace("$", "")),
        rating=int(product.select_one("p[data-rating]")["data-rating"]),
        num_of_reviews=int(product.select_one(".review-count").text.split()[0])
    )


def get_phones_products() -> list[Product]:
    text = requests.get(PHONES_URL).text
    soup = BeautifulSoup(text, "html.parser")
    products = soup.select(".card-body")
    return [parse_single_phones_product(product) for product in products]
