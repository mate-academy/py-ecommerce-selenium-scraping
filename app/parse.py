import csv
import time
from dataclasses import dataclass, fields, astuple
from typing import List
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from tqdm import tqdm

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")
URLS = {
    "home": HOME_URL,
    "computers": urljoin(HOME_URL, "computers"),
    "laptops": urljoin(HOME_URL, "computers/laptops"),
    "tablets": urljoin(HOME_URL, "computers/tablets"),
    "phones": urljoin(HOME_URL, "phones"),
    "touch": urljoin(HOME_URL, "phones/touch"),
}


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


PRODUCT_FIELDS = [field.name for field in fields(Product)]


def create_driver() -> WebDriver:
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    return webdriver.Chrome(options=chrome_options)


def single_product(product: BeautifulSoup) -> Product:
    return Product(
        title=product.select_one(".title")["title"],
        description=product.select_one(".description").text,
        price=float(product.select_one(".price").text.replace("$", "")),
        rating=len(product.select(".glyphicon-star")),
        num_of_reviews=int(
            product.select_one(".ratings > .pull-right").text.split()[0]
        ),
    )


def get_products(url: str, driver: WebDriver) -> List[Product]:
    driver.get(url)
    accept_cookies = driver.find_elements(By.CLASS_NAME, "acceptCookies")
    if accept_cookies:
        accept_cookies[0].click()
    more_buttons = driver.find_elements(
        By.CLASS_NAME, "ecomerce-items-scroll-more"
    )
    if more_buttons:
        more_button = more_buttons[0]
        while more_button.is_displayed():
            more_button.click()
            time.sleep(0.1)
    page = driver.page_source
    products = BeautifulSoup(page, "html.parser").select(".thumbnail")
    return [single_product(product) for product in products]


def write_products_to_csv(products: List[Product], name: str) -> None:
    with open(f"{name}.csv", "w", newline="", encoding="utf-8") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(PRODUCT_FIELDS)
        writer.writerows([astuple(product) for product in products])


def get_all_products() -> None:
    with create_driver() as driver:
        for filename, url in tqdm(URLS.items()):
            products = get_products(url, driver)
            write_products_to_csv(products, filename)


if __name__ == "__main__":
    get_all_products()
