import csv
from dataclasses import dataclass, astuple, fields
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common import (
    ElementClickInterceptedException,
    ElementNotInteractableException
)
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.wait import WebDriverWait

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")
COMPUTERS_URL = urljoin(BASE_URL, "/test-sites/e-commerce/more/computers")
LAPTOPS_URL = urljoin(
    BASE_URL, "/test-sites/e-commerce/more/computers/laptops"
)
TABLETS_URL = urljoin(
    BASE_URL, "/test-sites/e-commerce/more/computers/tablets"
)
PHONES_URL = urljoin(BASE_URL, "/test-sites/e-commerce/more/phones")
TOUCH_URL = urljoin(BASE_URL, "/test-sites/e-commerce/more/phones/touch")

urls_and_files = [
    (HOME_URL, "home.csv"),
    (COMPUTERS_URL, "computers.csv"),
    (LAPTOPS_URL, "laptops.csv"),
    (TABLETS_URL, "tablets.csv"),
    (PHONES_URL, "phones.csv"),
    (TOUCH_URL, "touch.csv"),
]


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


PRODUCT_FIELDS = [field.name for field in fields(Product)]


def parse_single_product(soup: BeautifulSoup) -> Product:
    return Product(
        title=soup.select_one("a")["title"],
        description=soup.select_one(".description").text.replace("\xa0", " "),
        price=float(soup.select_one(".price").text.replace("$", "")),
        rating=len(soup.select("span.ws-icon.ws-icon-star")),
        num_of_reviews=int(soup.select_one(".review-count").text.split()[0]),
    )


def get_products_from_soup(soup: BeautifulSoup) -> list[Product]:
    products = soup.select(".thumbnail")

    return [parse_single_product(product) for product in products]


def get_more_information_with_driver(url: str) -> list[Product]:
    driver = webdriver.Chrome()
    driver.get(url)

    accept_btn = WebDriverWait(driver, 10).until(
        ec.element_to_be_clickable((By.CLASS_NAME, "acceptCookies"))
    )
    accept_btn.click()
    button_more = WebDriverWait(driver, 10).until(
        ec.element_to_be_clickable((
            By.CLASS_NAME, "ecomerce-items-scroll-more")
        )
    )

    while button_more.is_displayed() and button_more.is_enabled():
        try:
            button_more.click()
        except ElementClickInterceptedException:
            print(f"Element click intercepted on page {url}")
            break
        except ElementNotInteractableException:
            print(f"Element not interactable on page {url}")
            break

    html_page = driver.page_source
    driver.quit()

    soup = BeautifulSoup(html_page, "html.parser")

    return get_products_from_soup(soup)


def process_products(url: str) -> list[Product]:
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")
    load_more = soup.select(".ecomerce-items-scroll-more")

    if load_more:
        return get_more_information_with_driver(url)

    return get_products_from_soup(soup)


def write_products_to_file(path: str, products: list[Product]) -> None:
    with open(path, "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(PRODUCT_FIELDS)
        writer.writerows([astuple(product) for product in products])


def fetch_and_save_product(url: str, file_name: str) -> list[Product]:
    products = process_products(url)
    write_products_to_file(file_name, products)

    return products


def get_all_products() -> None:
    for url, file_name in urls_and_files:
        fetch_and_save_product(url, file_name)


if __name__ == "__main__":
    get_all_products()
