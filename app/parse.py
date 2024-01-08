import csv
import time
from dataclasses import dataclass, astuple, fields
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

BASE_URL = "https://webscraper.io/"

CATEGORYS_LINKS = {
    "HOME_URL": urljoin(BASE_URL, "test-sites/e-commerce/more/"),
    "PHONES_URL": urljoin(BASE_URL, "/test-sites/e-commerce/more/phones"),
    "PHONES_TOUCH_URL": urljoin(
        BASE_URL, "/test-sites/e-commerce/more/phones/touch"
    ),
    "COMPUTERS_URL": urljoin(
        BASE_URL, "/test-sites/e-commerce/more/computers"
    ),
    "TABLETS_URL": urljoin(
        BASE_URL, "/test-sites/e-commerce/more/computers/tablets"
    ),
    "LAPTOPS_URL": urljoin(
        BASE_URL, "test-sites/e-commerce/more/computers/laptops"
    ),
}

PRODUCTS_OUTPUT_CSV_PATH = "products.csv"


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int
    additional_info: dict


PRODUCT_FIELDS = [field.name for field in fields(Product)]


_driver: WebDriver | None = None


def get_driver() -> WebDriver:
    return _driver


def set_driver(new_driver: WebDriver) -> None:
    global _driver
    _driver = new_driver


def parse_hdd_block_prices(
    product_soup: BeautifulSoup,
) -> dict[str, float]:
    detailed_url = urljoin(BASE_URL, product_soup.select_one(".title")["href"])
    driver = get_driver()
    driver.get(detailed_url)
    try:
        swatches = driver.find_element(By.CLASS_NAME, "swatches")
        buttons = swatches.find_elements(By.TAG_NAME, "button")
        prices = {}
        for button in buttons:
            if not button.get_property("disabled"):
                button.click()
                prices[button.get_property("value")] = float(
                    driver.find_element(By.CLASS_NAME, "price").text.replace(
                        "$", ""
                    )
                )
    except Exception as e:
        prices = None
    return prices


def parse_single_product(product_soup: BeautifulSoup) -> Product:
    hdd_prices = parse_hdd_block_prices(product_soup)
    return Product(
        title=product_soup.select_one(".title")["title"],
        description=product_soup.select_one(".description").text,
        price=float(product_soup.select_one(".price").text.replace("$", "")),
        rating=len(product_soup.select("span.ws-icon-star")),
        num_of_reviews=int(
            product_soup.select_one("p[class*=review-count]").text.split()[0]
        ),
        additional_info={"hdd_prices": hdd_prices},
    )


def get_single_page_products(page_soup: BeautifulSoup) -> [Product]:
    products = page_soup.select(".thumbnail")
    return [parse_single_product(product_soup) for product_soup in products]


def get_products_from_category(category_url: str) -> [Product]:
    driver = get_driver()
    driver.get(category_url)
    try:
        more_button = driver.find_element(
            By.CLASS_NAME, "ecomerce-items-scroll-more"
        )
    except Exception as e:
        more_button = None
    if more_button:
        try:
            while True:
                if more_button.is_displayed():
                    more_button.click()
        except Exception as e:
            print(e)

    page_content = driver.page_source
    page_soup = BeautifulSoup(page_content, "html.parser")
    all_products = get_single_page_products(page_soup)

    return all_products


def write_products_to_csv(products: [Product]) -> None:
    with open(PRODUCTS_OUTPUT_CSV_PATH, "w") as file:
        writer = csv.writer(file)
        writer.writerow(PRODUCT_FIELDS)
        writer.writerows([astuple(product) for product in products])


def get_all_products() -> None:
    all_products = []
    with webdriver.Chrome() as new_driver:
        set_driver(new_driver)
        for category_url in CATEGORYS_LINKS.values():
            all_products.extend(get_products_from_category(category_url))

    write_products_to_csv(all_products)


if __name__ == "__main__":
    get_all_products()
