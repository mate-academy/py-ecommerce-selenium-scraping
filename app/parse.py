import csv
import logging
import sys
import time
from dataclasses import dataclass, fields, astuple
from datetime import datetime
from typing import Optional
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as EC
from tqdm import tqdm


BASE_URL = "https://webscraper.io/"

URLS = {
    "home": urljoin(BASE_URL, "test-sites/e-commerce/more/"),
    "computers": urljoin(BASE_URL, "test-sites/e-commerce/more/computers"),
    "laptops": urljoin(
        BASE_URL, "test-sites/e-commerce/more/computers/laptops"
    ),
    "tablets": urljoin(
        BASE_URL, "test-sites/e-commerce/more/computers/tablets"
    ),
    "phones": urljoin(BASE_URL, "test-sites/e-commerce/more/phones"),
    "touch": urljoin(BASE_URL, "test-sites/e-commerce/more/phones/touch"),
}

logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)8s]: %(message)s",
    handlers=[
        logging.FileHandler("parser.log"),
        logging.StreamHandler(sys.stdout),
    ],
)


class WebDriverSingleton:
    instance: Optional[webdriver.Chrome] = None
    options: Options = Options()

    @classmethod
    def get_instance(cls) -> webdriver.Chrome:
        if cls.instance is None:
            cls.options.add_argument("--headless")
            cls.instance = webdriver.Chrome(options=cls.options)

        return cls.instance


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


CSV_FIELDS = [field.name for field in fields(Product)]


def accept_cookies(page_url):
    new_driver = WebDriverSingleton.get_instance()
    new_driver.get(page_url)

    try:
        wait = WebDriverWait(new_driver, 10)
        accept_button = wait.until(
            EC.element_to_be_clickable((By.CLASS_NAME, "acceptCookies"))
        )
        accept_button.click()
    except (NoSuchElementException, TimeoutException):
        logging.info(
            f"No accept cookies button found, proceeding. "
            f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )


def press_more_button(page_url) -> str:
    new_driver = WebDriverSingleton.get_instance()
    new_driver.get(page_url)

    try:
        wait = WebDriverWait(new_driver, 10)
        more_button = wait.until(
            EC.element_to_be_clickable(
                (By.CLASS_NAME, "ecomerce-items-scroll-more")
            )
        )

        while more_button:
            more_button.click()
            time.sleep(5)
            more_button = wait.until(
                EC.element_to_be_clickable(
                    (By.CLASS_NAME, "ecomerce-items-scroll-more")
                )
            )
    except (NoSuchElementException, TimeoutException):
        logging.info(
            f"Reach the bottom of page.  "
            f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )

    page = new_driver.page_source
    return page


def parse_single_product(product_soup: BeautifulSoup) -> Product:
    return Product(
        title=product_soup.select_one(".title").text,
        description=product_soup.select_one(".description").text,
        price=float(product_soup.select_one(".price").text.replace("$", "")),
        rating=len(product_soup.select(".ws-icon-star")),
        num_of_reviews=int(
            product_soup.select_one(".review-count").text.split(" ")[0]
        ),
    )


def get_products_on_page(page_soup: BeautifulSoup) -> [Product]:
    products = page_soup.select(".card-body")
    logging.info(
        f"Found {len(products)} items. "
        f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )
    return [parse_single_product(product) for product in products]


def get_all_products() -> None:

    for csv_name, url in tqdm(URLS.items(), desc="Processing URLs"):
        logging.info(
            f"Processing {url}."
            f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        accept_cookies(url)
        products = []
        page = requests.get(url).content
        page_soup = BeautifulSoup(page, "html.parser")
        more_button = page_soup.select_one(".ecomerce-items-scroll-more")

        if more_button:
            page = press_more_button(url)
            page_soup = BeautifulSoup(page, "html.parser")

        products.extend(get_products_on_page(page_soup))

        csv_output(products, csv_name)


def csv_output(products: [Product], csv_name: str) -> None:
    filename = csv_name + ".csv"

    with open(filename, "w") as file:
        writer = csv.writer(file)
        writer.writerow(CSV_FIELDS)
        writer.writerows([astuple(product) for product in products])
        logging.info(
            f"Wrote {len(products)} instances to {filename}. "
            f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )


if __name__ == "__main__":
    driver = WebDriverSingleton.get_instance()
    with driver as session:
        get_all_products()
