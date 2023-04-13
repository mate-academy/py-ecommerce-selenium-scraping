import os
from dataclasses import dataclass
from urllib.parse import urljoin

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


def get_all_products() -> None:
    list_of_products = ["phones",
                        "computers",
                        "home",
                        "laptops",
                        "tablets",
                        "touch"]
    for product in list_of_products:
        os.system(f"scrapy crawl {product} -O {product}.csv")


if __name__ == "__main__":
    get_all_products()
