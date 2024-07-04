from dataclasses import dataclass, fields
from typing import List
from urllib.parse import urljoin
import csv
import time

from bs4 import BeautifulSoup, Tag
from selenium import webdriver
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import (NoSuchElementException,
                                        ElementClickInterceptedException)

BU = "https://webscraper.io/"
URLS = {
    "home": urljoin(BU, "test-sites/e-commerce/more"),
    "computers": urljoin(BU, "test-sites/e-commerce/more/computers"),
    "laptops": urljoin(BU, "test-sites/e-commerce/more/computers/laptops"),
    "tablets": urljoin(BU, "test-sites/e-commerce/more/computers/tablets"),
    "phones": urljoin(BU, "test-sites/e-commerce/more/phones"),
    "touch": urljoin(BU, "test-sites/e-commerce/more/phones/touch"),
}


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


FIELDS = [field.name for field in fields(Product)]


def get_one_product(product: Tag) -> Product:
    return Product(
        title=product.select_one(".title")["title"],
        description=product.select_one(".description").get_text(strip=True),
        price=float(product.select_one(".price").text.replace("$", "")),
        rating=len(product.select(".ratings .ws-icon-star")),
        num_of_reviews=int(product.select_one(".review-count").text.split()[0])
    )


def get_products_from_page(page_url: str, driver: WebDriver) -> list[Product]:
    try:
        driver.get(page_url)
        cookies = driver.find_elements(By.CLASS_NAME, "acceptCookies")
        if cookies:
            cookies[0].click()
    except (NoSuchElementException, ElementClickInterceptedException) as e:
        print(f"An error occurred while handling cookies: {e}")

    try:
        buttons = driver.find_elements(
            By.CLASS_NAME, "ecomerce-items-scroll-more")
        if buttons:
            while buttons[0].is_displayed():
                buttons[0].click()
                time.sleep(0.2)
    except (NoSuchElementException, ElementClickInterceptedException) as e:
        print(f"An error occurred while clicking load more buttons: {e}")

    soup = BeautifulSoup(driver.page_source, "html.parser")
    products = soup.select(".thumbnail")
    return [get_one_product(product) for product in products]


def save_datas(file_path: str, products: List[Product]) -> None:
    with open(file_path, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(FIELDS)
        for product in products:
            writer.writerow([
                product.title,
                product.description,
                product.price,
                product.rating,
                product.num_of_reviews
            ])


def get_all_products() -> None:
    with webdriver.Chrome() as driver:
        for name, url in URLS.items():
            products = get_products_from_page(url, driver)
            file_name = f"{name}.csv"
            save_datas(file_name, products)


if __name__ == "__main__":
    get_all_products()
