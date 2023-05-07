import csv
import time

from dataclasses import dataclass, fields, astuple
from urllib.parse import urljoin
from selenium import webdriver
from selenium.common import (NoSuchElementException,
                             ElementNotInteractableException)
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from bs4 import BeautifulSoup

BASE_URL = "https://webscraper.io/"
URLS = {
    "home": "test-sites/e-commerce/more/",
    "phones": "test-sites/e-commerce/more/phones",
    "touch": "test-sites/e-commerce/more/phones/touch",
    "computers": "test-sites/e-commerce/more/computers",
    "tablets": "test-sites/e-commerce/more/computers/tablets",
    "laptops": "test-sites/e-commerce/more/computers/laptops",
}


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


PRODUCT_FIELDS = [field.name for field in fields(Product)]


def up_driver() -> webdriver:
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    return webdriver.Chrome(options=chrome_options)


def parse_single_product(product_soup: BeautifulSoup) -> Product:

    return Product(
        title=product_soup.select_one(".title")["title"],
        description=(
            product_soup.select_one(".description").text.replace("\xa0", " ")
        ),
        price=float(product_soup.select_one(".price").text.replace("$", "")),
        rating=len(product_soup.select(".glyphicon-star")),
        num_of_reviews=int(
            product_soup.select_one(".ratings").text.split()[0]
        ),
    )


def cookies(driver: WebDriver) -> None:
    try:
        driver.find_element(By.CLASS_NAME, "acceptCookies").click()
    except NoSuchElementException:
        pass


def get_all_information(driver: WebDriver) -> None:
    while True:
        try:
            driver.find_element(By.CLASS_NAME,
                                "ecomerce-items-scroll-more").click()
            time.sleep(0.5)
        except (NoSuchElementException, ElementNotInteractableException):
            break


def parsing(url: str, driver: WebDriver) -> list[Product]:
    driver.get(url)

    cookies(driver)
    get_all_information(driver)

    page = driver.page_source
    page_soup = BeautifulSoup(page, "html.parser")
    products = page_soup.select(".thumbnail")

    return [parse_single_product(product) for product in products]


def write_products_to_csv(name: str, products: [Product]) -> None:
    with open(name, "w") as file:
        writer = csv.writer(file)
        writer.writerow(PRODUCT_FIELDS)
        writer.writerows([astuple(product) for product in products])


def get_all_products() -> None:
    driver = up_driver()
    with driver:
        for file_name, url in URLS.items():
            products = parsing(urljoin(BASE_URL, url), driver)
            write_products_to_csv(f"{file_name}.csv", products)


if __name__ == "__main__":
    get_all_products()
