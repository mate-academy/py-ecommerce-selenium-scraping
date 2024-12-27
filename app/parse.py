import csv
import time
from dataclasses import dataclass, fields, astuple
from urllib.parse import urljoin

import requests
from bs4 import Tag, BeautifulSoup
from selenium import webdriver

from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")
COMPUTERS_URL = urljoin(HOME_URL, "computers/")
LAPTOPS_URL = urljoin(COMPUTERS_URL, "laptops")
TABLETS_URL = urljoin(COMPUTERS_URL, "tablets")
PHONES_URL = urljoin(HOME_URL, "phones/")
TOUCH_URL = urljoin(PHONES_URL, "touch")


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


PRODUCT_FIELDS = tuple(field.name for field in fields(Product))

_driver: WebDriver | None = None


def get_driver() -> WebDriver:
    return _driver


def set_driver(new_driver: WebDriver) -> None:
    global _driver
    _driver = new_driver


def scrape_one_product(product: Tag) -> Product:
    return Product(
        title=product.select_one(".title")["title"],
        description=product.select_one(".description").text.strip().replace(
            "\xa0", " "
        ),
        price=float(product.select_one(".price").text.lstrip("$")),
        rating=len(product.select(".ws-icon-star")),
        num_of_reviews=int(
            product.select_one(".review-count").text.split(" ")[0]
        ),
    )


def get_soup(url: str, session: requests.Session) -> BeautifulSoup:
    response = session.get(url)
    return BeautifulSoup(response.content, "html.parser")


def parse_one_page(url: str) -> [Product]:
    session = requests.Session()
    soup = get_soup(url, session)
    return [
        scrape_one_product(product)
        for product in soup.select(".product-wrapper")
    ]


def create_csv_file(
        path_csv_file: str,
        product_fields: tuple = PRODUCT_FIELDS
) -> None:
    with open(path_csv_file, "w") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(product_fields)


def append_to_csv(path_csv_file: str, products: [Product]) -> None:
    with open(path_csv_file, "a") as csv_file:
        writer = csv.writer(csv_file)
        for product in products:
            writer.writerow(astuple(product))


def create_and_write_csv(
        path_csv_file: str,
        url: str,
        product_fields: tuple = PRODUCT_FIELDS
) -> None:
    products = parse_one_page(url)
    create_csv_file(path_csv_file, product_fields)
    append_to_csv(path_csv_file, products)


def parse_and_write_page_with_js(
        driver: WebDriver,
        url: str,
        csv_path: str
) -> None:
    driver.get(url)

    time.sleep(1)

    if driver.find_elements(By.CSS_SELECTOR, ".acceptCookies"):
        cookie_button = driver.find_element(By.CSS_SELECTOR, ".acceptCookies")
        driver.execute_script("arguments[0].click();", cookie_button)

    button_more = driver.find_element(
        By.CSS_SELECTOR, ".ecomerce-items-scroll-more"
    )

    while True:
        time.sleep(1)
        if button_more.get_attribute("style") == "display: none;":
            break
        driver.execute_script("arguments[0].click();", button_more)

    page_html = driver.page_source

    soup = BeautifulSoup(page_html, "html.parser")
    products = [
        scrape_one_product(product)
        for product in soup.select(".product-wrapper")
    ]
    create_csv_file(csv_path)
    append_to_csv(csv_path, products)


def get_all_products() -> None:
    with webdriver.Chrome() as driver:
        set_driver(driver)

        create_and_write_csv("home.csv", HOME_URL)
        create_and_write_csv("computers.csv", COMPUTERS_URL)
        create_and_write_csv("phones.csv", PHONES_URL)

        parse_and_write_page_with_js(driver, TOUCH_URL, "touch.csv")
        parse_and_write_page_with_js(driver, TABLETS_URL, "tablets.csv")
        parse_and_write_page_with_js(driver, LAPTOPS_URL, "laptops.csv")


if __name__ == "__main__":
    get_all_products()
