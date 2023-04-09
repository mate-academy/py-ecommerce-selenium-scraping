import csv
import logging
import sys
from dataclasses import dataclass, fields, astuple
import time
from urllib.parse import urljoin
from bs4 import BeautifulSoup, Tag
from selenium import webdriver
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
import requests


BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")
URLS = {
    "home": "test-sites/e-commerce/more",
    "computers": "test-sites/e-commerce/more/computers",
    "laptops": "test-sites/e-commerce/more/computers/laptops",
    "tablets": "test-sites/e-commerce/more/computers/tablets",
    "phones": "test-sites/e-commerce/more/phones",
    "touch": "test-sites/e-commerce/more/phones/touch"
}


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int
    additional_info: dict


PRODUCT_FIELD = [field.name for field in fields(Product)]


logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)8s]: %(message)s",
    handlers=[logging.FileHandler("parser.log"),
              logging.StreamHandler(sys.stdout),
              ],
)

_driver: WebDriver | None


def get_driver() -> WebDriver:
    return _driver


def set_driver(new_driver: WebDriver) -> None:
    global _driver
    _driver = new_driver


def get_single_product(product_soup: Tag) -> Product:
    additional_info = parse_product_prices(
            product_soup.select_one(".title")["href"]
        )
    if additional_info == {}:
        additional_info = {}
    return Product(
        title=product_soup.select_one(".title")["title"],
        description=product_soup.select_one(".description").text,
        price=float(product_soup.select_one(
            ".price").text.replace("$", "")),
        rating=len(product_soup.select(".glyphicon-star")),
        num_of_reviews=int(product_soup.select_one(
            ".ratings > p.pull-right").text.split()[0]
                           ),
        additional_info=additional_info
    )


def get_page_of_product(url_product: str) -> [Product]:
    _driver = get_driver()
    url = urljoin(BASE_URL, url_product)
    _driver.get(url)

    try:
        accept_cookies_button = _driver.find_element(
            By.CLASS_NAME, "acceptCookies"
        )
        if accept_cookies_button:
            accept_cookies_button.click()
            time.sleep(0.1)
    except:
        pass

    try:
        more_button = _driver.find_element(
            By.CLASS_NAME, "ecomerce-items-scroll-more"
        )

        if more_button:
            while more_button.value_of_css_property(
                    "display") == "block":
                more_button.click()
                time.sleep(0.1)
    except:
        pass

    page = _driver.page_source
    soup = BeautifulSoup(page, "html.parser")

    products = soup.select(".thumbnail")
    return [get_single_product(product_) for product_ in products]


def parse_product_prices(product_url: str) -> dict:
    _driver = get_driver()
    _driver.get(urljoin(BASE_URL, product_url))
    prices_data = {}
    try:
        swatches = _driver.find_element(By.CLASS_NAME, "swatches")
        prices_data = {}
        buttons = swatches.find_elements(By.TAG_NAME, "button")
        for button in buttons:

            if not button.get_property("disabled"):
                button.click()
                price = float(_driver.find_element(
                    By.CLASS_NAME, "price").text.replace("$", ""))
                prices_data[button.get_property("value")] = price
        return prices_data
    except Exception:
        pass
    return prices_data


def get_all_products() -> [Product]:
    with webdriver.Chrome() as new_driver:
        set_driver(new_driver)
        for key, value in URLS.items():
            products = get_page_of_product(str(value))
            output_csv_path = str(key) + ".csv"
            with open(
                    output_csv_path,
                    "w+", newline="", encoding="UTF-8") as file:
                writer = csv.writer(file)
                writer.writerow(PRODUCT_FIELD)
                writer.writerows([astuple(product_) for product_ in products])


if __name__ == "__main__":
    get_all_products()
