from __future__ import annotations

import time
from dataclasses import dataclass, fields, astuple
from urllib.parse import urljoin
import csv
from bs4 import BeautifulSoup, Tag
from selenium import webdriver
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By


BASE_URL = "https://webscraper.io/test-sites/e-commerce/more/"
URLS = {
    "home": BASE_URL,
    "computers": urljoin(BASE_URL, "computers/"),
    "laptops": urljoin(BASE_URL, "computers/laptops"),
    "tablets": urljoin(BASE_URL, "computers/tablets"),
    "phones": urljoin(BASE_URL, "phones/"),
    "touch": urljoin(BASE_URL, "phones/touch"),
}


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int

    @classmethod
    def parse_single_product(cls, product: Tag) -> Product:
        return cls(
            title=product.select_one(".title")["title"],
            description=product.select_one(".description").text.replace(
                "\xa0", " "
            ),
            price=float(product.select_one("h4.price").text.replace("$", "")),
            rating=len(product.select(".glyphicon-star")),
            num_of_reviews=int(
                product.select_one("p.pull-right").text.split()[0]
            ),
        )

    @classmethod
    def get_page_products(
        cls, page_url: str, driver: WebDriver
    ) -> list[Product]:
        driver.get(page_url)
        cookies = driver.find_elements(By.CLASS_NAME, "acceptCookies")

        if cookies:
            cookies[0].click()

        button_more = driver.find_elements(
            By.CLASS_NAME, "ecomerce-items-scroll-more"
        )

        if button_more:
            while button_more[0].is_displayed():
                button_more[0].click()
                time.sleep(0.1)

        page = driver.page_source
        page_soup = BeautifulSoup(page, "html.parser")

        products = page_soup.select(".thumbnail")

        return [cls.parse_single_product(product) for product in products]


PRODUCT_FIELDS = [field.name for field in fields(Product)]


def write_products_to_csv(products: [Product], output_csv_path: str) -> None:
    with open(output_csv_path, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(PRODUCT_FIELDS)
        writer.writerows([astuple(product) for product in products])


def get_all_products() -> None:
    with webdriver.Chrome() as driver:
        for name, url in URLS.items():
            write_products_to_csv(
                products=Product.get_page_products(url, driver),
                output_csv_path=f"{name}.csv",
            )


if __name__ == "__main__":
    get_all_products()
