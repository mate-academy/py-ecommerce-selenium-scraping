import csv
import time
from dataclasses import dataclass, fields, astuple
from typing import List
from urllib.parse import urljoin

from bs4 import BeautifulSoup, Tag
from selenium import webdriver
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By

BASE_URL = "https://webscraper.io/test-sites/e-commerce/more/"
URLS = {
    "home": BASE_URL,
    "computers": urljoin(BASE_URL, "computers"),
    "laptops": urljoin(BASE_URL,
                       "computers/laptops"),
    "tablets": urljoin(BASE_URL,
                       "computers/tablets"),
    "phones": urljoin(BASE_URL, "phones"),
    "touch": urljoin(BASE_URL, "phones/touch"),
}


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


PRODUCT_DETAILS = [field.name for field in fields(Product)]


def parse_single_product(product: Tag) -> Product:
    return Product(
        title=product.select_one(".title")["title"],
        description=product.select_one(".description").text.replace(
            "\xa0", " "
        ),
        price=float(product.select_one(".price").text.replace("$", "")),
        rating=len(product.select(".ratings > p .glyphicon-star")),
        num_of_reviews=int(
            product.select_one(".ratings > p.pull-right").text.split()[0]
        ),
    )


def parse_products(url: str, driver: webdriver) -> List[Product]:
    driver.get(url)
    cookies = driver.find_elements(By.CLASS_NAME, "acceptCookies")
    if cookies:
        cookies[0].click()

    more_button = driver.find_elements(
        By.CLASS_NAME, "ecomerce-items-scroll-more"
    )
    if more_button:
        while more_button[0].is_displayed():
            more_button[0].click()
            time.sleep(0.1)

    soup = BeautifulSoup(driver.page_source, "html.parser")
    products = soup.select(".thumbnail")

    return [parse_single_product(product) for product in products]


def write_to_files(param: str, url: str, driver: WebDriver) -> None:
    with open(param, "w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(PRODUCT_DETAILS)
        products = parse_products(url, driver)
        writer.writerows([astuple(product) for product in products])


def get_all_products() -> None:
    pass
    with webdriver.Chrome() as driver:
        for name, url in URLS.items():
            write_to_files(f"{name}.csv", url, driver)


if __name__ == "__main__":
    get_all_products()
