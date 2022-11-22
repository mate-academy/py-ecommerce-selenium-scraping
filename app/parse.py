import csv
from dataclasses import dataclass, fields, astuple
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more")
COMPUTERS_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/computers")
LAPTOPS_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/computers/laptops")
TABLES_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/computers/tablets")
PHONES_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/phones")
TOUCH_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/phones/touch")

ALL_URL_FOR_THIS_TACK = [HOME_URL, COMPUTERS_URL, LAPTOPS_URL, TABLES_URL, PHONES_URL, TOUCH_URL]


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
        rating=int(product_soup.select_one("p[data-rating]")["data-rating"]) if product_soup.select_one("p[data-rating]") else len(product_soup.select(".glyphicon-star")),
        num_of_reviews=int(product_soup.select_one(".ratings > p.pull-right").text.split()[0])
    )


def get_all_products() -> None:

    for url in ALL_URL_FOR_THIS_TACK:
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

            soup = BeautifulSoup(page_source, 'html.parser')

        products = soup.select(".thumbnail")

        all_products = [parse_single_product(product_soup) for product_soup in products]

        file_name = "home.csv" if url.split('/')[-1] == "more" else f"{url.split('/')[-1]}.csv"

        with open(file_name, "w", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(PRODUCT_FIELDS)
            writer.writerows([astuple(product) for product in all_products])


if __name__ == "__main__":
    with webdriver.Chrome() as new_driver:
        set_driver(new_driver)
        get_all_products()
