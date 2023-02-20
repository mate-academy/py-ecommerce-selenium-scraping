import csv
import os
import time
from dataclasses import dataclass, fields, astuple
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")
COMPUTER_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/computers")
LAPTOPS_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/computers/laptops")
TABLETS_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/computers/tablets")
PHONE_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/phones")
TOUCH_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/phones/touch")

urls = {
    "home.csv": HOME_URL,
    "computers.csv": COMPUTER_URL,
    "laptops.csv": LAPTOPS_URL,
    "tablets.csv": TABLETS_URL,
    "phones.csv": PHONE_URL,
    "touch.csv": TOUCH_URL,
}


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


_driver: WebDriver | None = None


def get_driver() -> WebDriver:
    return _driver


def set_driver(new_driver: WebDriver) -> None:
    global _driver
    _driver = new_driver


def parse_single_product(product_soup: webdriver) -> Product:
    return Product(
        title=product_soup.select_one(".title")["title"],
        description=product_soup.select_one(".description").text,
        price=float(product_soup.select_one(".price").text.replace("$", "")),
        rating=int(len(product_soup.select(".glyphicon"))),
        num_of_reviews=int(
            product_soup.select_one(".ratings > p").text.split()[0]
        ),
    )


def get_page_soup(url: str) -> list[Product]:
    page = requests.get(url).content
    page_soup = BeautifulSoup(page, "html.parser")

    if page_soup.select_one(".ecomerce-items-scroll-more"):
        with webdriver.Chrome() as new_driver:
            set_driver(new_driver)
            driver = get_driver()
            driver.get(url)
            button = driver.find_element(
                By.CLASS_NAME, "ecomerce-items-scroll-more"
            )
            driver.find_element(By.CLASS_NAME, "acceptCookies").click()

            while not button.get_property("style"):
                button.click()
                time.sleep(0.1)

                button = driver.find_element(
                    By.CLASS_NAME, "ecomerce-items-scroll-more"
                )

            with open("index.html", "w", encoding="cp1251") as file:
                file.write(driver.page_source)

        with open("index.html") as file:
            page = file.read().replace("&nbsp;", " ")
        os.remove("index.html")

        page_soup = BeautifulSoup(page, "html.parser")
        return [parse_single_product(page)
                for page in page_soup.select(".thumbnail")]

    page_soup = page_soup.select(".thumbnail")
    return [parse_single_product(page) for page in page_soup]


def write_products_to_csv(name: str, products: [Product]) -> None:
    product_fields = [field.name for field in fields(Product)]
    with open(name, "w", newline="", encoding="cp1251") as file:
        writer = csv.writer(file)
        writer.writerow(product_fields)
        writer.writerows([astuple(product) for product in products])


def get_all_products() -> None:
    for name, url in urls.items():
        write_products_to_csv(name, get_page_soup(url))


if __name__ == "__main__":
    start = time.perf_counter()
    get_all_products()
    print(f"Elapsed: {time.perf_counter() - start}")
