from dataclasses import dataclass
from typing import Self
from urllib.parse import urljoin

import requests
from bs4 import Tag, BeautifulSoup

BASE_URL = "https://webscraper.io/test-sites/e-commerce/more/"
URLS = {
    "home": BASE_URL,
    "computers": urljoin(BASE_URL, "computers/"),
    "laptops": urljoin(BASE_URL, "computers/laptops"),
    "tablets": urljoin(BASE_URL, "computers/tablets"),
    "phones": urljoin(BASE_URL, "phones/"),
    "touch": urljoin(BASE_URL, "phones/touch")
}


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int

    @classmethod
    def parse_single_product(cls, product: Tag) -> Self:
        single_product_data = dict(
            title=product.select_one(".title")["title"],
            description=product.select_one(".description").text,
            price=float(product.select_one(".price").text.replace("$", "")),
            rating=len(product.select(".glyphicon-star")),
            num_of_reviews=int(
                product.select_one("p.pull-right").text.split()[0]
            ),
        )
        return cls(**single_product_data)


def parse_single_page(page_url: str) -> list[Product]:
    page_content = requests.get(page_url).content
    base_soup = BeautifulSoup(page_content, "html.parser")

    page_products_soup = base_soup.select(".thumbnail")

    all_page_quotes = [
        Product.parse_single_product(product)
        for product in page_products_soup
    ]

    return all_page_quotes


def get_all_products() -> None:
    pass


if __name__ == "__main__":
    get_all_products()
