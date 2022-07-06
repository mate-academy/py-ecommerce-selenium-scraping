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


def get_all_products():
    pass


if __name__ == "__main__":
    get_all_products()
