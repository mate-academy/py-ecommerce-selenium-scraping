import csv
import time
from dataclasses import dataclass, fields, astuple
from urllib.parse import urljoin

from selenium import webdriver
from selenium.common import (
    NoSuchElementException,
    TimeoutException,
    ElementClickInterceptedException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as ex_con
from selenium.webdriver.support.wait import WebDriverWait

BASE_URL = "http://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")
PAGES_TO_PARSE = {
    "home": "",
    "computers": "computers/",
    "laptops": "computers/laptops",
    "tablets": "computers/tablets",
    "phones": "phones/",
    "touch": "phones/touch",
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


PRODUCTS_FIELDS = [field.name for field in fields(Product)]


def get_single_product(product: WebElement) -> Product:
    return Product(
        title=product.find_element(By.CLASS_NAME, "title").get_attribute(
            "title"
        ),
        description=product.find_element(By.CLASS_NAME, "description").text,
        price=float(
            product.find_element(By.CLASS_NAME, "price").text.lstrip("$")
        ),
        rating=len(product.find_elements(By.CLASS_NAME, "ws-icon-star")),
        num_of_reviews=int(
            product.find_element(
                By.CSS_SELECTOR, '[itemprop="reviewCount"]'
            ).text
        ),
    )


def get_page_products(page_url: str) -> list[Product]:
    driver = get_driver()
    driver.get(page_url)
    try:
        cookies_button = driver.find_element(By.CSS_SELECTOR, ".acceptCookies")
        cookies_button.click()
    except NoSuchElementException:
        pass

    while True:
        try:
            button = WebDriverWait(driver, 2).until(
                ex_con.element_to_be_clickable(
                    (By.CSS_SELECTOR, ".ecomerce-items-scroll-more")
                )
            )
            button.click()
            time.sleep(0.1)
        except (TimeoutException, ElementClickInterceptedException):
            break

    products = driver.find_elements(By.CSS_SELECTOR, ".product-wrapper")
    return [get_single_product(product) for product in products]


def write_products_to_csv(products: list[Product], file_name: str) -> None:
    with open(f"{file_name}.csv", "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(PRODUCTS_FIELDS)
        writer.writerows([astuple(product) for product in products])


def get_all_products() -> None:
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")

    with webdriver.Chrome(options=options) as driver:
        set_driver(driver)
        for category, path in PAGES_TO_PARSE.items():
            print(f"Scrapping {category} page...")
            url = urljoin(HOME_URL, path)
            write_products_to_csv(get_page_products(url), category)


if __name__ == "__main__":
    get_all_products()
