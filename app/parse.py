import csv
from dataclasses import dataclass, astuple
from typing import Generator
from urllib.parse import urljoin
import requests

from bs4 import BeautifulSoup
from tqdm import tqdm

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")
COMPUTERS_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/computers")
PHONES_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/phones")
LAPTOPS_URL = urljoin(
    BASE_URL,
    "test-sites/e-commerce/static/computers/laptops"
)
TABLETS_URL = urljoin(
    BASE_URL,
    "test-sites/e-commerce/static/computers/tablets"
)
TOUCH_URL = urljoin(BASE_URL, "test-sites/e-commerce/static/computers/touch")


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


def parse_page(page: BeautifulSoup) -> list[Product]:
    result = []
    products = page.select(".card.thumbnail")

    for product in products:
        title = product.select_one("[itemprop='name']").text.strip()
        description = product.select_one(
            "[itemprop='description']").text.strip()
        price = float(
            product.select_one(
                "[itemprop='price']").text.strip().lstrip("$")
        )
        rating = len(product.select("p[data-rating] span.ws-icon-star"))
        num_of_reviews = int(
            product.select_one("[itemprop='reviewCount']").text.strip()
        )

        result.append(Product(
            title=title,
            description=description,
            price=price,
            rating=rating,
            num_of_reviews=num_of_reviews
        ))
    return result


def get_products(product_url: str) -> list[Product]:
    result = []
    for page in tqdm(page_generator_single(product_url)):
        result.extend(parse_page(page))
    return result


def get_phones() -> list[Product]:
    result = []
    for page in tqdm(page_generator_single(PHONES_URL)):
        result.extend(parse_page(page))
    return result


def get_laptops() -> list[Product]:
    result = []
    for page in tqdm(page_generator_commerce(LAPTOPS_URL)):
        result.extend(parse_page(page))
    return result


def get_tablets() -> list[Product]:
    result = []
    for page in tqdm(page_generator_commerce(TABLETS_URL)):
        result.extend(parse_page(page))
    return result


def get_touch() -> list[Product]:
    result = []
    for page in tqdm(page_generator_commerce(TOUCH_URL)):
        result.extend(parse_page(page))
    return result


def get_home() -> list[Product]:
    result = []
    for page in tqdm(page_generator_single(HOME_URL)):
        result.extend(parse_page(page))
    return result


def page_generator_single(url: str) -> Generator[BeautifulSoup, None, None]:
    content = fetch_page_content(url)
    if content:
        yield BeautifulSoup(content, "lxml")


def page_generator_commerce(url: str) -> Generator[BeautifulSoup, None, None]:
    """
    Generator for paginated e-commerce pages (e.g. laptops, computers)
    """
    page_counter = 1
    while True:
        page_url = f"{url}?page={page_counter}"
        content = fetch_page_content(page_url)
        if not content:
            break

        soup = BeautifulSoup(content, "lxml")
        products = soup.select(".card.thumbnail")
        if not products:
            break

        yield soup
        page_counter += 1


def fetch_page_content(url: str) -> bytes | None:
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.content
    except requests.RequestException as e:
        print(e)


def export_to_csv(products: list[Product], output_csv_path: str) -> None:
    with open(output_csv_path, "w", encoding="utf-8", newline="") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(
            ["title", "description", "price", "rating", "num_of_reviews"]
        )
        writer.writerows(
            [[str(v) for v in astuple(product)] for product in products]
        )


def get_all_products() -> None:
    home_page_info = get_home()
    export_to_csv(home_page_info, "home.csv")
    computers_page_info = get_products(COMPUTERS_URL)
    export_to_csv(computers_page_info, "computers.csv")
    phones_page_info = get_products(PHONES_URL)
    export_to_csv(phones_page_info, "phones.csv")
    laptops_page_info = get_products(LAPTOPS_URL)
    export_to_csv(laptops_page_info, "laptops.csv")
    tablets_page_info = get_products(TABLETS_URL)
    export_to_csv(tablets_page_info, "tablets.csv")
    touch_page_info = get_products(TOUCH_URL)
    export_to_csv(touch_page_info, "touch.csv")


if __name__ == "__main__":
    get_all_products()
