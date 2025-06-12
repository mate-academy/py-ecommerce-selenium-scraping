from typing import List
from urllib.parse import urljoin
import time
import csv
from dataclasses import dataclass, asdict

from selenium.webdriver.remote.webelement import WebElement
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.common.exceptions import NoSuchElementException, TimeoutException


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


def accept_cookies(driver: WebElement) -> None:
    try:
        wait = WebDriverWait(driver, 10)
        btn = wait.until(
            ec.element_to_be_clickable((By.CLASS_NAME, "acceptCookies"))
        )
        btn.click()
    except (NoSuchElementException, TimeoutException):
        return


def scroll_page(driver: WebElement) -> None:
    while True:
        try:
            btn = driver.find_element(
                By.CSS_SELECTOR, ".ecomerce-items-scroll-more"
            )
            if btn.is_displayed():
                btn.click()
                time.sleep(1)
            else:
                break
        except NoSuchElementException:
            break


def has_scroll_button(driver: WebElement) -> None:
    try:
        scroll_page(driver)
        time.sleep(1)
    except NoSuchElementException:
        return


def write_to_csv(file_name: str, products: List[Product]) -> None:
    fields = [field.name for field in Product.__dataclass_fields__.values()]
    with open(file_name, "w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(fields)
        writer.writerows([asdict(product).values() for product in products])


BASE_URL = "https://webscraper.io/"
URLS = {
    "home": urljoin(BASE_URL, "test-sites/e-commerce/more/"),
    "computers": urljoin(BASE_URL, "test-sites/e-commerce/more/computers"),
    "laptops": urljoin(
        BASE_URL, "test-sites/e-commerce/more/computers/laptops"
    ),
    "tablets": urljoin(
        BASE_URL, "test-sites/e-commerce/more/computers/tablets"
    ),
    "phones": urljoin(BASE_URL, "test-sites/e-commerce/more/phones"),
    "touch": urljoin(BASE_URL, "test-sites/e-commerce/more/phones/touch"),
}


def parse_single_product(product: WebElement) -> Product:
    return Product(
        title=product.find_element(
            By.CSS_SELECTOR, ".caption > h4 > a"
        ).get_attribute("title"),
        description=product.find_element(
            By.CSS_SELECTOR, ".caption > .description"
        ).text,
        price=float(
            product.find_element(
                By.CSS_SELECTOR, ".caption > .price"
            ).text.replace("$", "")
        ),
        rating=len(
            product.find_elements(
                By.CSS_SELECTOR, ".ratings > p:nth-of-type(2) > span"
            )
        ),
        num_of_reviews=int(
            product.find_element(
                By.CSS_SELECTOR, ".ratings > .review-count"
            ).text.replace("reviews", "")
        ),
    )


def get_page_with_products(url: str) -> List[Product]:
    with webdriver.Chrome() as driver:
        driver.get(url)
        accept_cookies(driver)
        has_scroll_button(driver)
        products = driver.find_elements(By.CLASS_NAME, "thumbnail")
        return [parse_single_product(p) for p in products]


def get_all_products() -> None:
    for key, url in URLS.items():
        products = get_page_with_products(url)
        write_to_csv(f"{key}.csv", products)


if __name__ == "__main__":
    get_all_products()
