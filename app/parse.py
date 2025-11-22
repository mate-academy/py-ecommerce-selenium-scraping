import csv
import time
from dataclasses import dataclass, fields, astuple

from selenium import webdriver
from selenium.common import NoSuchElementException, ElementNotInteractableException, ElementClickInterceptedException
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from urllib.parse import urljoin

import requests
from bs4 import Tag, BeautifulSoup

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")

COMPUTERS_URL = urljoin(HOME_URL, "computers/")
LAPTOPS_URL = urljoin(COMPUTERS_URL, "laptops")
TABLETS_URL = urljoin(COMPUTERS_URL, "tablets")

PHONES_URL = urljoin(HOME_URL, "phones/")
TOUCH_URL = urljoin(PHONES_URL, "touch")

PAGES_URL = {
    HOME_URL: "home.csv",
    COMPUTERS_URL: "computers.csv",
    LAPTOPS_URL: "laptops.csv",
    TABLETS_URL: "tablets.csv",
    PHONES_URL: "phones.csv",
    TOUCH_URL: "touch.csv"
}

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


PRODUCT_FIELDS = [product.name for product in fields(Product)]


def parse_single_product(product: Tag) -> Product:
    return Product(
        title=product.select_one(".title")["title"],
        description=product.select_one(".description").text,
        price=float(product.select_one(".price").text.replace("$", "")),
        rating=int(len(product.select("span.ws-icon-star"))),
        num_of_reviews=int(product.select_one(".review-count").text.split()[0])
    )


def get_page_products(input_url: str) -> [Product]:
    text = requests.get(input_url).content
    soup = BeautifulSoup(text, "html.parser")

    show_more_button = soup.select_one(".btn")

    if not show_more_button:
        products = soup.select(".card-body")
        return [parse_single_product(p) for p in products]

    driver = get_driver()
    driver.get(input_url)

    try:
        driver.find_element(By.CLASS_NAME, "acceptCookies").click()
    except NoSuchElementException:
        pass
    except ElementNotInteractableException:
        pass

    while True:
        try:
            element_more = driver.find_element(By.CLASS_NAME, "btn")

            driver.execute_script("arguments[0].scrollIntoView(true);", element_more)
            time.sleep(0.3)

            element_more.click()
            time.sleep(0.5)

        except NoSuchElementException:
            break

    soup = BeautifulSoup(driver.page_source, "html.parser")
    products = soup.select(".card-body")
    return [parse_single_product(p) for p in products]


def write_products_to_csv(link_url: str, filename: str) -> None:
    products = get_page_products(link_url)

    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(PRODUCT_FIELDS)
        writer.writerows([astuple(product) for product in products])


def get_all_products() -> None:
    with webdriver.Chrome() as driver:
        set_driver(driver)
        for key_url, value_filename in PAGES_URL.items():
            write_products_to_csv(key_url, value_filename)


if __name__ == "__main__":
    get_all_products()
