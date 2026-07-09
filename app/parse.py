from dataclasses import dataclass, fields, astuple
from urllib.parse import urljoin
import csv
import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    NoSuchElementException,
    ElementClickInterceptedException,
)


BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")

PAGES = {
    "home": HOME_URL,
    "computers": urljoin(BASE_URL, "test-sites/e-commerce/more/computers"),
    "laptops": urljoin(BASE_URL, "test-sites/e-commerce/more/computers/laptops"),
    "tablets": urljoin(BASE_URL, "test-sites/e-commerce/more/computers/tablets"),
    "phones": urljoin(BASE_URL, "test-sites/e-commerce/more/phones"),
    "touch": urljoin(BASE_URL, "test-sites/e-commerce/more/phones/touch"),
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
    return webdriver.Chrome(options=options)


def parse_single_product(product: WebElement) -> Product:
    return Product(
        title=product.find_element(
            By.CLASS_NAME, "title"
        ).get_attribute("title"),
        description=product.find_element(
            By.CLASS_NAME, "description"
        ).text,
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


def accept_cookies(driver: webdriver.Chrome) -> None:
    try:
        button = driver.find_element(By.CLASS_NAME, "acceptCookies")
        button.click()
    except NoSuchElementException:
        pass


def click_more_until_end(driver: webdriver.Chrome) -> None:
    wait = WebDriverWait(driver, 10)

    while True:
        try:
            more_button = driver.find_element(
                By.CLASS_NAME, "ecomerce-items-scroll-more"
            )
        except NoSuchElementException:
            break

        if not more_button.is_displayed():
            break

        products_before = len(
            driver.find_elements(By.CLASS_NAME, "thumbnail")
        )

        driver.execute_script("arguments[0].click();", more_button)

        wait.until(
            lambda d: len(d.find_elements(By.CLASS_NAME, "thumbnail"))
            > products_before
        )


def get_single_page_products(driver: webdriver.Chrome, url: str) -> list[Product]:
    driver.get(url)
    accept_cookies(driver)
    click_more_until_end(driver)

    products = driver.find_elements(By.CLASS_NAME, "thumbnail")
    return [parse_single_product(product) for product in products]


def write_products_to_csv(products: list[Product], path: str) -> None:
    with open(path, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(PRODUCT_FIELDS)
        writer.writerows([astuple(product) for product in products])


def get_all_products() -> None:
    driver = get_driver()
    try:
        for name, url in PAGES.items():
            products = get_single_page_products(driver, url)
            write_products_to_csv(products, f"{name}.csv")
    finally:
        driver.quit()


if __name__ == "__main__":
    get_all_products()
