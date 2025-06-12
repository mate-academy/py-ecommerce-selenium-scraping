import csv
import logging
from dataclasses import dataclass, astuple
from typing import Generator, List
from urllib.parse import urljoin

from selenium import webdriver
from selenium.common import (
    NoSuchElementException,
    ElementNotInteractableException,
    ElementClickInterceptedException,
)
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")

URLS = {
    "laptops": urljoin(HOME_URL, "computers/laptops"),
    "home": HOME_URL,
    "computers": urljoin(HOME_URL, "computers"),
    "tablets": urljoin(HOME_URL, "computers/tablets"),
    "phones": urljoin(HOME_URL, "phones"),
    "touch": urljoin(HOME_URL, "phones/touch"),
}

logging.basicConfig(level=logging.INFO)

@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int

def parse_item(item: WebElement) -> Product:
    title = item.find_element(By.CSS_SELECTOR, ".title").get_attribute("title")
    description = item.find_element(By.CSS_SELECTOR, ".description").text
    price = _parse_price(item)
    rating = len(item.find_elements(By.CSS_SELECTOR, ".ws-icon-star"))
    num_of_reviews = int(item.find_element(By.CSS_SELECTOR, "[itemprop=reviewCount]").text)
    return Product(title, description, price, rating, num_of_reviews)

def _parse_price(item: WebElement) -> float:
    try:
        return float(item.find_element(By.CSS_SELECTOR, "span[itemprop=price]").text.replace("$", ""))
    except NoSuchElementException:
        try:
            return float(item.find_element(By.CSS_SELECTOR, ".price").text.replace("$", ""))
        except NoSuchElementException:
            return 0.0

def get_more_anchors(driver: WebDriver) -> Generator[WebElement, None, None]:
    while True:
        try:
            more_anchor = driver.find_element(By.CSS_SELECTOR, ".ecomerce-items-scroll-more")
            if more_anchor and "display: none;" not in more_anchor.get_attribute("style"):
                yield more_anchor
            else:
                break
        except NoSuchElementException:
            break

def parse_list_page(driver: WebDriver) -> List[Product]:
    for more_anchor in get_more_anchors(driver):
        try:
            more_anchor.click()
        except (ElementNotInteractableException, ElementClickInterceptedException):
            continue
    items = driver.find_elements(By.CSS_SELECTOR, ".product-wrapper")
    return [parse_item(item) for item in items]

def save_products_to_csv(products: List[Product], filename: str) -> None:
    with open(filename, "w", newline="") as result_file:
        writer = csv.writer(result_file)
        writer.writerow(Product.__dataclass_fields__.keys())
        for product in products:
            writer.writerow(astuple(product))

def process_page(driver: WebDriver, page: str, url: str) -> None:
    logging.info(f"Processing page: {page}")
    driver.get(url)
    _accept_cookies(driver)
    products = parse_list_page(driver)
    save_products_to_csv(products, f"{page}.csv")

def _accept_cookies(driver: WebDriver) -> None:
    try:
        accept_cookie_button = driver.find_element(By.CSS_SELECTOR, ".acceptCookies")
        accept_cookie_button.click()
    except NoSuchElementException:
        pass

def get_all_products() -> None:
    with webdriver.Chrome() as driver:
        for page, url in URLS.items():
            process_page(driver, page, url)

if __name__ == "__main__":
    get_all_products()