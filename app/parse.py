import csv
import sys
import time
import logging

from dataclasses import dataclass, astuple, fields
from urllib.parse import urljoin

from bs4 import BeautifulSoup, Tag

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")

URLS = {
    "home": HOME_URL,
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


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


PRODUCT_FIELDS = [field.name for field in fields(Product)]

logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)8s]: %(message)s",
    handlers=[
        logging.FileHandler("parser.log"),
        logging.StreamHandler(sys.stdout),
    ],
)


def get_driver() -> WebDriver:
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    driver = webdriver.Chrome(options=options)
    return driver


def parse_single_product(product_soup: Tag) -> Product:
    return Product(
        title=product_soup.select_one(".title")["title"],
        description=product_soup.select_one(".description").text,
        price=float(product_soup.select_one(".price").text.replace("$", "")),
        rating=len(product_soup.select(".ratings span")),
        num_of_reviews=int(
            product_soup.select_one(".review-count").text.split()[0]),
    )


def get_single_page_products(
        page_url: str,
        driver: WebDriver
) -> list[Product]:
    driver.get(page_url)
    cookies_button = driver.find_elements(By.CLASS_NAME, "acceptCookies")
    if cookies_button:
        cookies_button[0].click()

    more_button = driver.find_elements(
        By.CLASS_NAME,
        "ecomerce-items-scroll-more"
    )

    if more_button:
        more_button = more_button[0]
        while more_button.is_displayed():
            more_button.click()
            time.sleep(2)

    page_soup = BeautifulSoup(driver.page_source, "html.parser")

    products = page_soup.select(".thumbnail")
    return [parse_single_product(product_soup) for product_soup in products]


def write_products_to_csv(
        products: list[Product],
        output_csv_path: str
) -> None:
    with open(output_csv_path, "w", newline="", encoding="utf-8") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(PRODUCT_FIELDS)
        writer.writerows(astuple(product) for product in products)


def get_all_products() -> None:
    with get_driver() as new_driver:
        for name, page_url in URLS.items():
            print(f"Getting {name} products from {page_url}")
            all_products = get_single_page_products(page_url, new_driver)
            write_products_to_csv(all_products, f"{name}.csv")


if __name__ == "__main__":
    get_all_products()
