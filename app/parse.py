import csv
import os
from dataclasses import dataclass, astuple, fields
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common import (
    NoSuchElementException,
    TimeoutException,
    ElementNotInteractableException,
)
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.firefox import GeckoDriverManager


BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")

COMPUTERS_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/computers/")
LAPTOPS_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/computers/laptops")
TABLETS_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/computers/tablets")
PHONES_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/phones/")
TOUCHES_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/phones/touch")


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


PRODUCT_FIELDS = [field.name for field in fields(Product)]


def parse_single_product(product_soup: BeautifulSoup) -> Product:
    return Product(
        title=product_soup.select_one(".title")["title"],
        description=product_soup.select_one(".description").text,
        price=float(product_soup.select_one(".price").text.replace("$", "")),
        rating=len(product_soup.select(".ratings span.ws-icon.ws-icon-star")),
        num_of_reviews=int(
            product_soup.select_one(".ratings > p.float-end").text.split()[0]
        ),
    )


def get_page_products(url: str) -> list[Product]:
    print(f"Getting products from: {url}")
    options = Options()
    options.add_argument("--headless")

    service = Service(GeckoDriverManager().install())
    driver = webdriver.Firefox(service=service, options=options)
    driver.get(url)
    products = []

    try:
        while True:
            print("Fetching page source...")
            page_source = driver.page_source
            soup = BeautifulSoup(page_source, "html.parser")
            products_soup = soup.select(".thumbnail")
            print(f"Found {len(products_soup)} products on this page.")
            products.extend(
                [parse_single_product(product) for product in products_soup]
            )

            try:
                print("Looking for 'more' button...")
                more_button = WebDriverWait(driver, 5).until(
                    expected_conditions.presence_of_element_located(
                        (By.CLASS_NAME, "ecomerce-items-scroll-more")
                    )
                )
                if more_button.is_displayed():
                    print("Clicking 'more' button...")
                    more_button.click()
                else:
                    print("No more products to load.")
                    break
            except (
                NoSuchElementException,
                TimeoutException,
                ElementNotInteractableException,
            ):
                print("No 'more' button found or error occurred.")
                break
    finally:
        print("Quitting driver...")
        driver.quit()
    return products


def write_to_csv(products: list[Product], filename: str) -> None:
    with open(os.path.join(os.pardir, filename), "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(PRODUCT_FIELDS)
        writer.writerows([astuple(product) for product in products])


def get_all_products() -> None:
    urls = {
        HOME_URL: "home.csv",
        COMPUTERS_URL: "computers.csv",
        PHONES_URL: "phones.csv",
        LAPTOPS_URL: "laptops.csv",
        TABLETS_URL: "tablets.csv",
        TOUCHES_URL: "touch.csv",
    }

    for url, filename in urls.items():
        products = get_page_products(url)
        write_to_csv(products, filename)


if __name__ == "__main__":
    get_all_products()
