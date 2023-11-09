import asyncio
import logging
import sys
from csv import writer
from dataclasses import astuple, dataclass, fields
from urllib.parse import urljoin
from unicodedata import normalize

import httpx
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.firefox.options import Options


logging.basicConfig(
    level=logging.INFO,
    handlers=[
        logging.FileHandler("parser.log"),
        logging.StreamHandler(sys.stdout),
    ],
)


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")

COMPUTERS_URL = urljoin(HOME_URL, "computers/")
PHONES_URL = urljoin(HOME_URL, "phones/")
TOUCH_PHONES_URL = urljoin(HOME_URL, "phones/touch")
TABLETS_URL = urljoin(HOME_URL, "computers/tablets")
LAPTOPS_URL = urljoin(HOME_URL, "computers/laptops")

PRODUCT_FIELDS = [field.name for field in fields(Product)]
HOME_PAGE_PRODUCTS_FILENAME = "home.csv"
COMPUTERS_FILENAME = "computers.csv"
PHONES_FILENAME = "phones.csv"
TOUCH_PHONES_FILENAME = "touch.csv"
TABLETS_FILENAME = "tablets.csv"
LAPTOPS_FILENAME = "laptops.csv"


def get_product(product_soup: BeautifulSoup) -> Product:
    title = product_soup.select_one(".title")
    if title is None:
        raise ValueError("Product title is None")

    description = product_soup.select_one(".description")
    if description is None:
        raise ValueError("Product description is None")

    price = product_soup.select_one(".price")
    if price is None:
        raise ValueError("Product price is None")

    stars = product_soup.select(".ratings > p > span.ws-icon-star")
    if stars is None:
        raise ValueError("Product rating is None")

    reviews = product_soup.select_one(".review-count")
    if reviews is None:
        raise ValueError("Product reviews is None")
    num_of_reviews, _ = reviews.text.split()

    return Product(
        title=title["title"],
        description=normalize("NFKD", description.text),
        price=float(price.text.lstrip("$")),
        rating=len(stars),
        num_of_reviews=int(num_of_reviews),
    )


def get_products_from_page(page_soup: BeautifulSoup) -> list[Product]:
    products = page_soup.select(".product-wrapper > .card-body")
    return [get_product(product) for product in products]


async def get_products(url: str, client: httpx.AsyncClient) -> list[Product]:
    resp = await client.get(url)
    soup = BeautifulSoup(resp.content, "html.parser")
    return get_products_from_page(soup)


def get_products_with_pagination(url: str) -> list[Product]:
    options = Options()
    options.add_argument("--headless")
    with webdriver.Firefox(options=options) as driver:
        logging.info(f"Fetching {url}")
        driver.get(url)
        while buttons := driver.find_elements(
            By.CSS_SELECTOR,
            ".ecomerce-items-scroll-more:not([style*='display: none'])",
        ):
            button, *_ = buttons
            driver.execute_script("arguments[0].scrollIntoView();", button)
            wait = WebDriverWait(driver, 5)
            wait.until(ec.element_to_be_clickable(button)).click()
        soup = BeautifulSoup(driver.page_source, "html.parser")
        return get_products_from_page(soup)


def write_to_csv(
    objects: list, csv_path: str, fields: list[str] = PRODUCT_FIELDS
) -> None:
    with open(csv_path, "w", newline="") as csvfile:
        quotewriter = writer(csvfile)
        quotewriter.writerow(fields)
        quotewriter.writerows(astuple(obj) for obj in objects)


async def main() -> None:
    async with httpx.AsyncClient() as client:
        tasks = [
            get_products(HOME_URL, client),
            get_products(COMPUTERS_URL, client),
            get_products(PHONES_URL, client),
            asyncio.to_thread(get_products_with_pagination, LAPTOPS_URL),
            asyncio.to_thread(get_products_with_pagination, TABLETS_URL),
            asyncio.to_thread(get_products_with_pagination, TOUCH_PHONES_URL),
        ]
        (
            home_page_products,
            computers,
            phones,
            laptops,
            tablets,
            touch_phones,
        ) = await asyncio.gather(*tasks)
        write_to_csv(home_page_products, HOME_PAGE_PRODUCTS_FILENAME)
        write_to_csv(computers, COMPUTERS_FILENAME)
        write_to_csv(phones, PHONES_FILENAME)
        write_to_csv(laptops, LAPTOPS_FILENAME)
        write_to_csv(tablets, TABLETS_FILENAME)
        write_to_csv(touch_phones, TOUCH_PHONES_FILENAME)


def get_all_products() -> None:
    asyncio.run(main())


if __name__ == "__main__":
    get_all_products()
