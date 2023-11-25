from __future__ import annotations

import csv

from dataclasses import dataclass
from time import sleep
from urllib.parse import urljoin
from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")
filename_list = ["home", "computers", "phones", "tablets", "laptops", "touch"]
extra_url_list = [
    "",
    "computers",
    "phones",
    "computers/tablets",
    "computers/laptops",
    "phones/touch",
]


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


def get_all_from_page(products: list[BeautifulSoup]) -> [Product]:
    product_list = []

    for product in products:
        product_list.append(
            Product(
                title=product.select_one(".title")["title"],
                description=product.select_one(".description").text.replace(
                    " ",
                    " ",
                ),
                price=float(product.select_one(".price").text.replace(
                    "$",
                    "",
                )),
                rating=len(product.select(".ws-icon-star")),
                num_of_reviews=int(
                    product.select_one(".review-count").text.split()[0]
                ),
            )
        )

    return product_list


def get_page(extra_url: str) -> str:
    return urljoin(HOME_URL, extra_url)


def get_all_pages(extra_url: str) -> [Product]:
    page = get_page(extra_url)
    driver = get_driver()
    driver.get(page)
    sleep(1)

    cookie_button = driver.find_elements(By.CLASS_NAME, "acceptCookies")
    if cookie_button:
        cookie_button[0].click()

    pagination_button = driver.find_elements(
        By.CLASS_NAME,
        "ecomerce-items-scroll-more",
    )
    if pagination_button:
        pagination_button = pagination_button[0]
        while pagination_button.is_displayed():
            pagination_button.click()
            sleep(1)

    soup = BeautifulSoup(driver.page_source, "html.parser")

    products = soup.select(".thumbnail")
    return [product_soup for product_soup in products]


def write_to_csv(data_list: list[Product], filepath: str) -> None:
    with open(f"{filepath}.csv", "w", newline="") as productfile:
        csv_writer = csv.writer(productfile)

        csv_writer.writerow(
            ["title", "description", "price", "rating", "num_of_reviews"]
        )

        for data in data_list:
            csv_writer.writerow(
                [
                    data.title,
                    data.description,
                    data.price,
                    data.rating,
                    data.num_of_reviews,
                ]
            )


def get_all_products() -> None:
    for i in range(len(filename_list)):
        with webdriver.Chrome() as new_driver:
            set_driver(new_driver)
            product = get_all_from_page(get_all_pages(extra_url_list[i]))
            write_to_csv(product, filename_list[i])


if __name__ == "__main__":
    get_all_products()
