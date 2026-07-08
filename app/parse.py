import time
import csv
from dataclasses import astuple, dataclass, fields
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.by import By
from selenium import webdriver
from selenium.common.exceptions import (
    ElementClickInterceptedException,
    ElementNotInteractableException,
    NoSuchElementException,
)
from urllib.parse import urljoin


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
COOKIE_BUTTON_SELECTORS = (".acceptCookies", "[data-tid='banner-accept']")


def accept_cookies(driver: webdriver.Chrome) -> None:
    for selector in COOKIE_BUTTON_SELECTORS:
        try:
            driver.find_element(By.CSS_SELECTOR, selector).click()
            return
        except (NoSuchElementException, ElementNotInteractableException):
            continue


def parse_single_product(product: WebElement) -> Product:
    return Product(
        title=product.find_element(
            By.CLASS_NAME, "title"
        ).get_attribute("title"),
        description=product.find_element(
            By.CLASS_NAME, "description"
        ).text,
        price=float(product.find_element(
            By.CLASS_NAME, "price"
        ).text.replace("$", "")),
        rating=len(product.find_elements(
            By.CLASS_NAME, "ws-icon-star"
        )),
        num_of_reviews=int(product.find_element(
            By.CLASS_NAME, "review-count"
        ).text.split()[0]),
    )


def click_more_button(driver: webdriver.Chrome) -> None:
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
        except (
                ElementClickInterceptedException,
                ElementNotInteractableException,
        ):
            accept_cookies(driver)
            driver.execute_script("arguments[0].click();", more_button)
        time.sleep(0.25)


def parse_page(driver: webdriver.Chrome, url: str) -> list[Product]:
    driver.get(url)
    accept_cookies(driver)
    click_more_button(driver)
    return [
        parse_single_product(product)
        for product in driver.find_elements(By.CLASS_NAME, "thumbnail")
    ]


def write_products_to_csv(
    products: list[Product], output_csv_path: str
) -> None:
    with open(output_csv_path, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(PRODUCT_FIELDS)
        writer.writerows(astuple(product) for product in products)


def get_all_products() -> None:
    with webdriver.Chrome() as driver:
        for name, url in PAGES.items():
            products = parse_page(driver, url)
            write_products_to_csv(products, f"{name}.csv")


if __name__ == "__main__":
    get_all_products()
