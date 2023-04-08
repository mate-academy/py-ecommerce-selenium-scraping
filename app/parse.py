import logging
import sys
from dataclasses import dataclass, fields
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup, Tag
from selenium import webdriver
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By


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

_driver: WebDriver | None = None


def get_driver() -> WebDriver:
    return _driver


def set_driver(new_driver: WebDriver) -> None:
    global _driver
    _driver = new_driver


def get_single_product(product_soup: BeautifulSoup) -> Product:
    return Product(
        title=product_soup.select_one(".title")["title"],
        description=product_soup.select_one(".description").text,
        price=float(product_soup.select_one(".price").text.replace("$", "")),
        rating=len(product_soup.select(".glyphicon-star")),
        num_of_reviews=int(product_soup.select_one(".ratings > p.pull-right").text.split()[0]),
        additional_info=parse_product_prices(
            product_soup.select_one(".title")["href"]
        ),
    )


def get_page_of_product() -> [Product]:

    driver = get_driver()
    url = "https://webscraper.io/test-sites/e-commerce/more"
    driver.get(url)

    try:
        more_btn = driver.find_element(
            By.CLASS_NAME,
            "ecomerce-items-scroll-more"
        )

        if more_btn:

            try:

                more_btn.click()
            except Exception:
                pass
    except Exception:
        pass

    page = requests.get(url).content
    soup = BeautifulSoup(page, "html.parser")
    products = soup.select(".thumbnail")
    return [get_single_product(product) for product in products]


def parse_product_prices(product_url: str) -> dict:
    driver = get_driver()
    driver.get(urljoin(BASE_URL, product_url))
    prices_data = {}
    try:
        swatches = driver.find_element(By.CLASS_NAME, "swatches")
        prices_data = {}
        buttons = swatches.find_elements(By.TAG_NAME, "button")
        for button in buttons:

            if not button.get_property("disabled"):
                button.click()
                price = float(driver.find_element(By.CLASS_NAME, "price").text.replace("$", ""))
                prices_data[button.get_property("value")] = price
        return prices_data
    except Exception:
        pass
    return prices_data



# def get_all_products() -> [Product]:
#
#         return get_page_of_product("https://webscraper.io/test-sites/e-commerce/more/phones/touch")


if __name__ == "__main__":
    with webdriver.Chrome() as new_driver:
        set_driver(new_driver)
        print(get_page_of_product())
