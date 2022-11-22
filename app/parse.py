import csv
from dataclasses import dataclass, fields, astuple
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

HOME_URL = "https://webscraper.io/test-sites/e-commerce/more/"
COMPUTERS_URL = urljoin(HOME_URL, "computers")
LAPTOPS_URL = urljoin(HOME_URL, "computers/laptops")
TABLES_URL = urljoin(HOME_URL, "computers/tablets")
PHONES_URL = urljoin(HOME_URL, "phones")
TOUCH_URL = urljoin(HOME_URL, "phones/touch")

ALL_URLS = [HOME_URL, COMPUTERS_URL, LAPTOPS_URL, TABLES_URL, PHONES_URL, TOUCH_URL]

FILE_NAMES = [
    "home.csv" if url.split("/")[-1] == "" else f"{url.split('/')[-1]}.csv"
    for url in ALL_URLS
]


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


PRODUCT_FIELDS = [field.name for field in fields(Product)]


_driver = None


def get_driver() -> WebDriver:
    return _driver


def set_driver(new_driver: WebDriver) -> None:
    global _driver
    _driver = new_driver


def parse_single_product(product_soup: BeautifulSoup) -> Product:
    return Product(
        title=product_soup.select_one(".title")["title"],
        description=product_soup.select_one(".description").text,
        price=float(product_soup.select_one(".price").text.replace("$", "")),
        rating=int(product_soup.select_one("p[data-rating]")["data-rating"])
        if product_soup.select_one("p[data-rating]")
        else len(product_soup.select(".glyphicon-star")),
        num_of_reviews=int(
            product_soup.select_one(".ratings > p.pull-right").text.split()[0]
        ),
    )


def parse(url: str) -> [Product]:

    page = requests.get(url).content
    soup = BeautifulSoup(page, "html.parser")

    if soup.select_one(".ecomerce-items-scroll-more"):
        driver = get_driver()
        driver.get(url)

        while soup.select_one(".ecomerce-items-scroll-more"):

            button = driver.find_element(By.CLASS_NAME, "ecomerce-items-scroll-more")

            driver.execute_script("arguments[0].click();", button)

            if button.get_attribute("style"):
                break

        page_source = driver.page_source

        soup = BeautifulSoup(page_source, "html.parser")

    products = soup.select(".thumbnail")

    all_products = [parse_single_product(product_soup) for product_soup in products]

    return all_products


def get_all_products(file_name: str, all_products: [Product]) -> None:
    with open(file_name, "w", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(PRODUCT_FIELDS)
        writer.writerows([astuple(product) for product in all_products])


if __name__ == "__main__":
    with webdriver.Chrome() as new_driver:
        set_driver(new_driver)

        for count, url in enumerate(ALL_URLS):
            all_products = parse(url)
            get_all_products(file_name=FILE_NAMES[count], all_products=all_products)
