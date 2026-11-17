import csv
import time
from dataclasses import astuple, dataclass, fields
from urllib.parse import urljoin

from selenium import webdriver
from selenium.common.exceptions import (
    ElementClickInterceptedException,
    NoSuchElementException,
    TimeoutException,
)
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")

PAGES = {
    "home": HOME_URL,
    "computers": urljoin(HOME_URL, "computers"),
    "laptops": urljoin(HOME_URL, "computers/laptops"),
    "tablets": urljoin(HOME_URL, "computers/tablets"),
    "phones": urljoin(HOME_URL, "phones"),
    "touch": urljoin(HOME_URL, "phones/touch"),
}


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


PRODUCT_FIELDS = [field.name for field in fields(Product)]


def get_driver() -> webdriver.Chrome:
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.page_load_strategy = "eager"
    driver = webdriver.Chrome(options=options)
    driver.set_page_load_timeout(30)
    return driver


def accept_cookies(driver: webdriver.Chrome) -> None:
    try:
        button = WebDriverWait(driver, 5).until(
            ec.element_to_be_clickable((By.CLASS_NAME, "acceptCookies"))
        )
        button.click()
    except TimeoutException:
        pass


def load_all_products(driver: webdriver.Chrome) -> None:
    while True:
        try:
            more_button = driver.find_element(
                By.CLASS_NAME, "ecomerce-items-scroll-more"
            )
        except NoSuchElementException:
            return
        if not more_button.is_displayed():
            return
        try:
            more_button.click()
        except ElementClickInterceptedException:
            accept_cookies(driver)
            continue
        time.sleep(0.2)


def parse_single_product(product: WebElement) -> Product:
    return Product(
        title=product.find_element(
            By.CLASS_NAME, "title"
        ).get_attribute("title"),
        description=product.find_element(By.CLASS_NAME, "description").text,
        price=float(
            product.find_element(By.CLASS_NAME, "price").text.replace("$", "")
        ),
        rating=len(
            product.find_elements(By.CLASS_NAME, "ws-icon-star")
        ),
        num_of_reviews=int(
            product.find_element(
                By.CLASS_NAME, "review-count"
            ).text.split()[0]
        ),
    )


def get_single_page_products(
        driver: webdriver.Chrome, url: str
) -> list[Product]:
    driver.get(url)
    accept_cookies(driver)
    load_all_products(driver)
    products = driver.find_elements(By.CLASS_NAME, "product-wrapper")
    return [parse_single_product(product) for product in products]


def write_products_to_csv(name: str, products: list[Product]) -> None:
    with open(f"{name}.csv", "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(PRODUCT_FIELDS)
        writer.writerows(astuple(product) for product in products)


def get_all_products() -> None:
    driver = get_driver()
    try:
        for name, url in PAGES.items():
            products = get_single_page_products(driver, url)
            write_products_to_csv(name, products)
    finally:
        driver.quit()


if __name__ == "__main__":
    get_all_products()
