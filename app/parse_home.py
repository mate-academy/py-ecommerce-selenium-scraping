import requests
from bs4 import BeautifulSoup, Tag

from app.constants import HOME_URL
from app.models import Product


def parse_single_home_product(product: Tag) -> Product:
    return Product(
        title=product.select_one(".title")["title"],
        description=product.select_one(".description").text,
        price=float(product.select_one(".price").text.replace("$", "")),
        rating=int(product.select_one("p[data-rating]")["data-rating"]),
        num_of_reviews=int(product.select_one(".review-count").text.split()[0])
    )


def get_home_products() -> list[Product]:
    text = requests.get(HOME_URL).text
    soup = BeautifulSoup(text, "html.parser")
    products = soup.select(".card-body")
    return [parse_single_home_product(product) for product in products]
