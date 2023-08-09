from dataclasses import dataclass
from typing import Self
from urllib.parse import urljoin

from bs4 import Tag


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
    def get_single_product(cls, product: Tag) -> Self:
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


def get_all_products() -> None:
    pass


if __name__ == "__main__":
    get_all_products()
