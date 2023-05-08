from dataclasses import dataclass, fields, astuple
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By

import csv
import time


BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")

URLS = {
    "home": HOME_URL,
    "phones": urljoin(HOME_URL, "phones/"),
    "touch": urljoin(HOME_URL, "phones/touch"),
    "computers": urljoin(HOME_URL, "computers"),
    "tablets": urljoin(HOME_URL, "computers/tablets"),
    "laptops": urljoin(HOME_URL, "computers/laptops"),
}


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


PRODUCT_FIELD = [field.name for field in fields(Product)]


def parse_single_product(product_soup: BeautifulSoup) -> Product:
    return Product(
        title=product_soup.select_one(".title")["title"],
        description=product_soup.select_one(".description")
        .text.replace("\xa0", " "),
        price=float(product_soup.select_one(".price").text.replace("$", "")),
        rating=len(product_soup.select(".ratings > p .glyphicon-star")),
        num_of_reviews=int(
            product_soup.select_one(".ratings > p.pull-right").text.split()[0]
        )
    )


def parse_product(url: str, driver: webdriver) -> list:
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


def write_in_files(csv_path: str, url: str, driver: webdriver) -> None:
    with open(csv_path, "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(PRODUCT_FIELD)
        products = parse_product(url, driver)
        writer.writerows([astuple(product) for product in products])


def get_all_products() -> None:
    with webdriver.Chrome() as driver:
        for name, url in URLS.items():
            write_in_files(f"{name}.csv", url, driver)


if __name__ == "__main__":
    get_all_products()
