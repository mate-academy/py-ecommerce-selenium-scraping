import asyncio
import csv
from dataclasses import dataclass, asdict
from multiprocessing import Pool
from typing import List, Tuple

from bs4 import BeautifulSoup
from httpx import AsyncClient
from selenium import webdriver
from selenium.webdriver.common.by import By

from app.options import URLS, CHROME_OPTIONS
from app.utils import get_tasks, accept_cookies, scroll_more


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int

    def dict(self) -> dict:
        return {k: str(v) for k, v in asdict(self).items()}


def parse_page(soup: BeautifulSoup) -> Product:
    title = soup.select_one(".title.card-title").text
    price = float(soup.select_one(".price").text.replace("$", ""))
    description = soup.select_one(".description").text
    rating = len(soup.select(".ws-icon-star"))
    num_of_reviews = int(soup.select_one(".review-count").text.split(" ")[0])
    product = Product(
        title=title,
        description=description,
        price=price,
        rating=rating,
        num_of_reviews=num_of_reviews
    )
    return product


async def parse_pages(product_url_list: List[str]) -> List[Product]:
    async with AsyncClient() as client:
        soups = await asyncio.gather(*get_tasks(client, product_url_list))
    product_list = [parse_page(soup) for soup in soups]
    return product_list


def get_product_ulr_list(driver: webdriver.Chrome) -> List[str]:
    cards = driver.find_elements(By.CLASS_NAME, "card.thumbnail")
    product_url_list = [
        card.find_element(By.CLASS_NAME, "title").get_attribute("href")
        for card in cards
    ]
    return product_url_list


def make_csv_file(products: List[Product], filename: str) -> None:
    with open(
            file=f"{filename}.csv",
            mode="w",
            newline="") as csvfile:
        fieldnames = products[0].dict().keys()

        productwriter = csv.DictWriter(csvfile, fieldnames=fieldnames)
        productwriter.writeheader()

        for product in products:
            productwriter.writerow(product.dict())


def get_products_by_url(url: str, filename: str) -> None:
    with webdriver.Chrome(CHROME_OPTIONS) as driver:
        driver.get(url)
        accept_cookies(driver)
        scroll_more(driver)
        product_url_list = get_product_ulr_list(driver)
        products = asyncio.run(parse_pages(product_url_list))
        make_csv_file(products=products, filename=filename)


def get_products_by_url_wrapper(args: Tuple[str, str]) -> None:
    url, filename = args
    get_products_by_url(url, filename)


def get_all_products() -> None:
    mapped_urls = URLS.get_mapped_urls_filenames()
    with Pool() as pool:
        pool.map(get_products_by_url_wrapper, mapped_urls)


if __name__ == "__main__":
    get_all_products()
