import csv
import time
from dataclasses import dataclass, astuple
from typing import Generator
from urllib.parse import urljoin

from bs4 import BeautifulSoup, Tag
from selenium import webdriver
from selenium.common import (
    NoSuchElementException,
)
from selenium.webdriver.common.by import By

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


def extract_product(product: Tag) -> Product:
    title = product.select_one("a.title")["title"]
    description = product.select_one("p.description").text.replace("\xa0", " ")
    price = float(product.select_one("h4.price").text.replace("$", ""))
    rating = len(product.find_all("span", class_="ws-icon ws-icon-star"))
    rate_string = product.select_one("p.review-count").text
    num_of_reviews = int(
        "".join([number for number in rate_string if number.isnumeric()])
    )
    return Product(
        title=title,
        description=description,
        price=price,
        rating=rating,
        num_of_reviews=num_of_reviews,
    )


def parse_products(page_content: bytes, num: int) -> list[Product]:
    soup = BeautifulSoup(page_content, "html.parser")
    product_tags = soup.select(".product-wrapper")
    return [
        extract_product(product_tags[i]) for i in range(num, len(product_tags))
    ]


def page_generator(url: str) -> Generator[bytes, None, None]:
    driver = webdriver.Chrome()
    driver.get(url)
    cookie = driver.find_element(By.ID, "closeCookieBanner")
    pagination_button = ""
    if cookie:
        cookie.click()
    try:
        pagination_button = driver.find_element(
            By.CSS_SELECTOR,
            "a" ".btn.btn-lg.btn-block.btn-primary.ecomerce-items-scroll-more",
        )
    except NoSuchElementException:
        yield driver.page_source.encode("utf-8")

    if pagination_button:
        while True:
            try:
                time.sleep(1)
                display_style = pagination_button.value_of_css_property(
                    "display"
                )
                if display_style == "none":
                    yield driver.page_source.encode("utf-8")
                    break
                pagination_button.click()
                yield driver.page_source.encode("utf-8")
            except NoSuchElementException:
                break


def scrape_products(url) -> list[Product]:
    products = []
    num = 0
    for page in page_generator(url):
        new_products = parse_products(page, num)
        products.extend(new_products)
        num += len(new_products)
    return products


def write_to_file(url, products) -> None:
    file = url.split("/")[-1]
    if file == "":
        file = "home"
    with open(f"{file}.csv", "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(
            ["title", "description", "price", "rating", "num_of_reviews"]
        )
        writer.writerows([astuple(product) for product in products])


def get_all_products():
    pages_url = [
        urljoin(HOME_URL, "computers/laptops"),
        urljoin(HOME_URL, "computers/tablets"),
        urljoin(HOME_URL, "phones/touch"),
        urljoin(HOME_URL, "phones"),
        urljoin(HOME_URL, "computers"),
        HOME_URL,
    ]
    for page_url in pages_url:
        products = scrape_products(page_url)
        write_to_file(page_url, products)


if __name__ == "__main__":
    get_all_products()
