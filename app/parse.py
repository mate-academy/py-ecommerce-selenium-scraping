from dataclasses import dataclass, fields
from urllib.parse import urljoin

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")

COMPUTERS_URL = urljoin(HOME_URL, "computers/")
TABLETS_URL = urljoin(COMPUTERS_URL, "tablets/")
LAPTOPS_URL = urljoin(COMPUTERS_URL, "laptops/")

PHONES_URL = urljoin(HOME_URL, "phones/")
TOUCH_URL = urljoin(PHONES_URL, "touch/")


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


PRODUCT_FIELDS = [field.name for field in fields(Product)]


def get_all_products() -> None:
    pass


if __name__ == "__main__":
    get_all_products()
