import csv
import html
import time
from dataclasses import dataclass, astuple
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")
COMPUTERS_URL = urljoin(BASE_URL, "/test-sites/e-commerce/more/computers")
LAPTOPS_URL = urljoin(
    BASE_URL,
    "/test-sites/e-commerce/more/computers/laptops"
)
TABLETS_URL = urljoin(
    BASE_URL,
    "/test-sites/e-commerce/more/computers/tablets"
)
PHONES_URL = urljoin(BASE_URL, "/test-sites/e-commerce/more/phones")
TOUCH_URL = urljoin(BASE_URL, "/test-sites/e-commerce/more/phones/touch")

URLS_AND_FILES = [
    (HOME_URL, "home.csv"),
    (COMPUTERS_URL, "computers.csv"),
    (LAPTOPS_URL, "laptops.csv"),
    (TABLETS_URL, "tablets.csv"),
    (PHONES_URL, "phones.csv"),
    (TOUCH_URL, "touch.csv")
]


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


def parse_single_product(soup: BeautifulSoup) -> Product:
    return Product(
        title=soup.select_one("a")["title"],
        description=html.unescape(
            soup
            .select_one(".description")
            .decode_contents()
            .replace("\xa0", " ")
        ),
        price=float(soup.select_one(".price").text.replace("$", "")),
        rating=len(soup.select("span.ws-icon.ws-icon-star")),
        num_of_reviews=int(soup.select_one(".review-count").text.split()[0]),
    )


def fetch_html(url: str) -> BeautifulSoup:
    response = requests.get(url)
    return BeautifulSoup(response.content, "html.parser")


def get_products_from_soup(soup: BeautifulSoup) -> list[Product]:
    products = soup.select(".thumbnail")
    return [parse_single_product(product) for product in products]


def press_button_more(url: str) -> list[Product]:
    driver = webdriver.Chrome()
    driver.get(url)

    button_more = driver.find_element(
        By.CLASS_NAME,
        "ecomerce-items-scroll-more"
    )
    style_attribute = button_more.get_attribute("style")

    accept_btn = driver.find_element(By.CLASS_NAME, "acceptCookies")
    accept_btn.click()

    while not style_attribute:
        button_more.click()
        time.sleep(1)
        style_attribute = button_more.get_attribute("style")

    html_page = driver.page_source
    driver.close()

    soup = BeautifulSoup(html_page, "html.parser")

    return get_products_from_soup(soup)


def check_button_more(url: str) -> list[Product]:
    soup = fetch_html(url)
    button = soup.select(".ecomerce-items-scroll-more")
    if button:
        return press_button_more(url)
    return get_products_from_soup(soup)


def write_products_to_file(path: str, products: list[Product]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow([
            "title",
            "description",
            "price",
            "rating",
            "num_of_reviews"
        ])
        writer.writerows([astuple(product) for product in products])


def get_products_by_type(url: str, file_name: str) -> list[Product]:
    products = check_button_more(url)
    write_products_to_file(file_name, products)
    return products


def get_all_products() -> None:
    for url, file_name in URLS_AND_FILES:
        get_products_by_type(url, file_name)


if __name__ == "__main__":
    get_all_products()
