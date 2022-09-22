import csv
import time
from dataclasses import dataclass, fields, astuple
from urllib.parse import urljoin

import selenium
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")
LIST_URLS = [
    (HOME_URL, "home.csv"),
    (urljoin(HOME_URL, "computers"), "computers.csv"),
    (urljoin(HOME_URL, "computers/laptops"), "laptops.csv"),
    (urljoin(HOME_URL, "computers/tablets"), "tablets.csv"),
    (urljoin(HOME_URL, "phones"), "phones.csv"),
    (urljoin(HOME_URL, "phones/touch"), "touch.csv"),
]


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


PRODUCT_FIELDS = [field.name for field in fields(Product)]


class WebDriver:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        self.driver = webdriver.Chrome()


def get_single_product(driver: WebDriver()) -> Product:
    return Product(
        title=driver.find_element(By.CLASS_NAME, "title").get_attribute("title"),
        description=driver.find_element(By.CLASS_NAME, "description").text,
        price=float(driver.find_element(By.CLASS_NAME, "price").text.replace("$", "")),
        rating=int(len(driver.find_elements(By.CLASS_NAME, "glyphicon-star"))),
        num_of_reviews=int(driver.find_element(By.CSS_SELECTOR, ".ratings .pull-right").text.split()[0]),
    )


def parse_single_page_product(url, driver: WebDriver()) -> [Product]:
    driver.get(url)

    try:
        cookies = driver.find_element(By.CLASS_NAME, "acceptCookies")
        if cookies.is_displayed():
            cookies.click()
    except selenium.common.exceptions.NoSuchElementException:
        pass
    try:
        more_button = driver.find_element(By.CLASS_NAME, "ecomerce-items-scroll-more")
    except selenium.common.exceptions.NoSuchElementException:
        pass
    else:
        while more_button.is_displayed():
            more_button.click()
            time.sleep(0.1)
    finally:
        products = driver.find_elements(By.CLASS_NAME, "thumbnail")
        return [get_single_product(product) for product in products]


def write_products_to_csv(products: [Product], output_csv_path: str) -> None:
    with open(output_csv_path, "w", newline="",) as file:

        writer = csv.writer(file)
        writer.writerow(PRODUCT_FIELDS)
        writer.writerows([astuple(product) for product in products])


def get_all_products():
    with WebDriver().driver as new_driver:
        for page in LIST_URLS:
            write_products_to_csv(parse_single_page_product(page[0], new_driver), page[1])


if __name__ == "__main__":
    get_all_products()

