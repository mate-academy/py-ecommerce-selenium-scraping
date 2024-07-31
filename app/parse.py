import csv
import time
from dataclasses import dataclass, asdict
from typing import List
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")
COMPUTER_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/computers/")
LAPTOP_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/computers/laptops/")
TABLET_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/computers/tablets/")
PHONE_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/phones/")
TOUCH_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/phones/touch/")


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


def parse_single_product(soup: BeautifulSoup) -> Product:
    return Product(
        title=soup.select_one(".title")["title"],
        description=soup.select_one(".description").text,
        price=float(soup.select_one(".price").text.replace("$", "")),
        rating=int(soup.select_one("p[data-rating]")["data-rating"]),
        num_of_reviews=int(soup.select_one(".ratings > p.float-end").text.split()[0]),
    )


def get_static_page_products(url: str) -> List[Product]:
    page = requests.get(url).text
    soup = BeautifulSoup(page, "html.parser")
    products_soup = soup.select(".thumbnail")
    return [parse_single_product(product) for product in products_soup]


def get_page_products_with_more_button(url: str) -> List[Product]:
    driver = webdriver.Chrome()
    driver.get(url)
    products = []

    while True:
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, "html.parser")
        products_soup = soup.select(".thumbnail")
        products.extend([parse_single_product(product) for product in products_soup])

        try:
            more_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CLASS_NAME, "ecomerce-items-scroll-more"))
            )
            driver.execute_script("arguments[0].click();", more_button)
            time.sleep(2)
        except Exception:
            break

    driver.quit()
    return products


def write_to_csv(products: List[Product], filename: str) -> None:
    with open(filename, "w", newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=Product.__annotations__.keys())
        writer.writeheader()
        for product in products:
            writer.writerow(asdict(product))


def get_all_products():
    urls = {
        HOME_URL: ("home.csv", False),
        COMPUTER_URL: ("computers.csv", False),
        LAPTOP_URL: ("laptops.csv", True),
        TABLET_URL: ("tablets.csv", True),
        PHONE_URL: ("phones.csv", False),
        TOUCH_URL: ("touch.csv", True),
    }

    for url, (filename, use_more_button) in urls.items():
        if use_more_button:
            products = get_page_products_with_more_button(url)
        else:
            products = get_static_page_products(url)
        write_to_csv(products, filename)


if __name__ == "__main__":
    get_all_products()
