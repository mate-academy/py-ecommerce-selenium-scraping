import logging
import csv
import time
from dataclasses import dataclass, fields
from typing import List
from urllib.parse import urljoin

from bs4 import BeautifulSoup, Tag
from selenium import webdriver
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)


BASE_URL = "https://webscraper.io/"
URLS = {
    "home": urljoin(BASE_URL,
                    "test-sites/e-commerce/more"),
    "computers": urljoin(BASE_URL,
                         "test-sites/e-commerce/more/computers"),
    "laptops": urljoin(BASE_URL,
                       "test-sites/e-commerce/more/computers/laptops"),
    "tablets": urljoin(BASE_URL,
                       "test-sites/e-commerce/more/computers/tablets"),
    "phones": urljoin(BASE_URL,
                      "test-sites/e-commerce/more/phones"),
    "touch": urljoin(BASE_URL,
                     "test-sites/e-commerce/more/phones/touch"),
}


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


PRODUCT_FIELDS = [field.name for field in fields(Product)]


def get_single_product(product: Tag) -> Product:
    return Product(
        title=product.select_one(".title")["title"],
        description=product.select_one(
            ".description"
        ).text.replace("\xa0", " ").replace("Â", ""),
        price=float(product.select_one(".price").text.replace("$", "")),
        rating=len(product.select(".ratings .ws-icon-star")),
        num_of_reviews=int(product.select_one(".review-count").text.split()[0])
    )


def get_products_from_page(page_url: str,
                           driver: WebDriver) -> list[Product]:
    driver.get(page_url)
    cookies = driver.find_elements(By.CLASS_NAME,
                                   "acceptCookies")

    if cookies:
        cookies[0].click()

    more_button = driver.find_elements(
        By.CLASS_NAME, "ecomerce-items-scroll-more"
    )

    if more_button:
        while more_button[0].is_displayed():
            more_button[0].click()
            time.sleep(0.1)

    soup = BeautifulSoup(driver.page_source,
                         "html.parser")
    products = soup.select(".thumbnail")

    return [get_single_product(product) for product in products]


def write_products_to_csv(file_path: str, products: List[Product]) -> None:
    with open(file_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(PRODUCT_FIELDS)
        for product in products:
            row = [
                product.title,
                product.description,
                product.price,
                product.rating,
                product.num_of_reviews
            ]
            writer.writerow(row)


def get_all_products() -> None:
    logging.info("Starting web scraping process...")
    with webdriver.Chrome() as driver:
        for name, url in URLS.items():
            logging.info(f"Scraping products from {name} page: {url}")
            products = get_products_from_page(url, driver)
            file_name = f"{name}.csv"
            write_products_to_csv(file_name, products)
            logging.info(f"Products from {name} "
                         f"page scraped and saved to {file_name}")
    logging.info("Web scraping process completed.")


if __name__ == "__main__":
    get_all_products()
