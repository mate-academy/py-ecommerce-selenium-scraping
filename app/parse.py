import csv
from contextlib import contextmanager
from dataclasses import dataclass, fields, astuple
from typing import Generator
from urllib.parse import urljoin

from selenium import webdriver
from selenium.common.exceptions import (
    ElementClickInterceptedException,
    StaleElementReferenceException,
    TimeoutException,
)
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait
from tqdm import tqdm


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

WAIT_TIMEOUT = 10

PRODUCT_SELECTOR = ".product-wrapper"
MORE_BUTTON_SELECTOR = ".ecomerce-items-scroll-more"
COOKIES_BUTTON_SELECTOR = ".acceptCookies"


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


PRODUCT_FIELDS = [field.name for field in fields(Product)]


@contextmanager
def create_driver() -> Generator[WebDriver, None, None]:
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    driver = webdriver.Chrome(options=options)
    try:
        yield driver
    finally:
        driver.quit()


def accept_cookies(driver: WebDriver) -> None:
    buttons = driver.find_elements(By.CSS_SELECTOR, COOKIES_BUTTON_SELECTOR)
    for button in buttons:
        if button.is_displayed():
            try:
                button.click()
            except ElementClickInterceptedException:
                driver.execute_script("arguments[0].click();", button)
            return


def load_all_products(driver: WebDriver) -> None:
    while True:
        buttons = driver.find_elements(By.CSS_SELECTOR, MORE_BUTTON_SELECTOR)
        if not buttons or not buttons[0].is_displayed():
            return

        loaded_before = len(
            driver.find_elements(By.CSS_SELECTOR, PRODUCT_SELECTOR)
        )
        accept_cookies(driver)
        try:
            driver.execute_script("arguments[0].click();", buttons[0])
            WebDriverWait(driver, WAIT_TIMEOUT).until(
                lambda drv: len(
                    drv.find_elements(By.CSS_SELECTOR, PRODUCT_SELECTOR)
                ) > loaded_before
            )
        except (StaleElementReferenceException, TimeoutException):
            return


def parse_product(element: WebElement) -> Product:
    title_element = element.find_element(By.CSS_SELECTOR, ".title")
    title = title_element.get_attribute("title") or title_element.text

    description = (
        element.find_element(By.CSS_SELECTOR, ".description")
        .get_attribute("textContent")
        .replace("\xa0", " ")
        .strip()
    )

    price = float(
        element.find_element(By.CSS_SELECTOR, ".price")
        .get_attribute("textContent")
        .strip()
        .lstrip("$")
    )

    rating = len(element.find_elements(By.CSS_SELECTOR, ".ws-icon-star"))

    num_of_reviews = int(
        element.find_element(By.CSS_SELECTOR, ".review-count")
        .get_attribute("textContent")
        .split()[0]
    )

    return Product(
        title=title,
        description=description,
        price=price,
        rating=rating,
        num_of_reviews=num_of_reviews,
    )


def parse_page(driver: WebDriver, url: str) -> list[Product]:
    driver.get(url)
    WebDriverWait(driver, WAIT_TIMEOUT).until(
        ec.presence_of_element_located((By.CSS_SELECTOR, PRODUCT_SELECTOR))
    )
    accept_cookies(driver)
    load_all_products(driver)

    elements = driver.find_elements(By.CSS_SELECTOR, PRODUCT_SELECTOR)
    return [parse_product(element) for element in elements]


def write_products_to_csv(products: list[Product], file_name: str) -> None:
    with open(file_name, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(PRODUCT_FIELDS)
        writer.writerows(astuple(product) for product in products)


def get_all_products() -> None:
    with create_driver() as driver:
        for name, url in tqdm(PAGES.items(), desc="Scraping pages"):
            products = parse_page(driver, url)
            write_products_to_csv(products, f"{name}.csv")


if __name__ == "__main__":
    get_all_products()
