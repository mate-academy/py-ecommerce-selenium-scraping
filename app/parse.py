import csv
import logging
import sys

from dataclasses import dataclass, fields, astuple
from selenium import webdriver
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup, Tag


BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/allinone")
LAPTOP_URL = urljoin(BASE_URL, "test-sites/e-commerce/static/computers/laptops")

_driver: WebDriver | None = None


def get_driver() -> WebDriver:
    return _driver


def set_driver(new_driver: WebDriver) -> None:
    global _driver
    _driver = new_driver


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int
    additional_info: dict


PRODUCT_FIELDS = [field.name for field in fields(Product)]

logging.basicConfig(
    level=logging.DEBUG,
    format="[%(levelname)8s]: %(message)s",
    handlers=[
        logging.FileHandler("parser.log"),
        logging.StreamHandler(sys.stdout),
    ]
)


def parse_hdd_block_prices(product_soup: Tag) -> dict[str, float]:
    absolute_url = urljoin(BASE_URL, product_soup.select_one(".title")["href"])
    driver = get_driver()
    driver.get(absolute_url)
    swatches = driver.find_element(By.CLASS_NAME, "swatches")
    buttons = swatches.find_elements(By.TAG_NAME, "button")
    prices = {}
    for button in buttons:
        if not button.get_property("disabled"):
            button.click()
            prices[button.get_property("value")] = float(
                driver.find_element(
                    By.CLASS_NAME, ".price"
                ).text.replace("$", "")
            )
    return prices


def parse_single_product(product: Tag) -> Product:
    hdd_prices = parse_hdd_block_prices(product)
    return Product(
        title=product.select_one(".title")["title"],
        description=product.select_one(".descriptoin").text,
        price=float(product.select_one(".price").text.replace("$", "")),
        rating=int(product.select_one("p[data-rating]")["data-rating"]),
        num_of_reviews=int(product.select_one(".review-count").text.split()[0]),
        additional_info={"hdd_prices": hdd_prices}
    )


def get_home_products() -> [Product]:
    text = requests.get(HOME_URL).content
    soup = BeautifulSoup(text, "html.parser")
    product = soup.select(".card-body")
    return [parse_single_product(product) for product in products]


def get_num_pages(page_soup: Tag) -> int:
    pagination = page_soup.select_one(".pagination")
    if pagination is None:
        return 1
    return int(pagination.select("li")[-2].text)


def get_single_page_products(page_soup: Tag) -> [Product]:
    products = page_soup.select(".cad-body")
    return [parse_single_product(product) for product in products]


def get_laptop_page_products() -> [Product]:
    logging.info("Start parsing laptops")
    text = requests.get(LAPTOP_URL).content
    first_page_soup = BeautifulSoup(text, "html.parser")

    all_products = get_single_page_products(first_page_soup)
    num_pages = get_num_pages(first_page_soup)
    for page_num in range(2, num_pages + 1):
        logging.info(f"Start parsing page #{page_num}")
        text = requests.get(LAPTOP_URL, {"page": page_num}).content
        next_page_soup = BeautifulSoup(text, "html.parser")
        all_products.extend(get_single_page_products(next_page_soup))
    return all_products


def write_products_to_csv(products: [Product]) -> None:
    with open("results.csv", "w") as f:
        writer = csv.writer(f)
        writer.writerow(PRODUCT_FIELDS)
        writer.writerows(([astuple(product) for product in products]))


def main():
    with webdriver.Chrome() as driver:
        set_driver(driver)
        write_products_to_csv(get_laptop_page_products())


if __name__ == "__main__":
    main()
