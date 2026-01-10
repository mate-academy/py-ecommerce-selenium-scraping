import csv
from dataclasses import dataclass
from typing import Optional, List
from urllib.parse import urljoin

import requests
from selenium import webdriver
from selenium.common import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from bs4 import Tag, BeautifulSoup
from selenium.webdriver.support.wait import WebDriverWait

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")
COMPUTERS_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/computers")
PHONES_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/phones")
LAPTOPS_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/computers/laptops")
TABLETS_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/computers/tablets")
TOUCH_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/phones/touch")


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


def accept_cookies_if_present(driver, timeout: int = 5) -> None:
    try:
        button = WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button.acceptCookies"))
        )
        driver.execute_script("arguments[0].click();", button)
    except (NoSuchElementException, TimeoutException):
        pass


def get_more_products_html(url) -> Optional[str]:
    driver = webdriver.Chrome()
    wait = WebDriverWait(driver, 15)

    try:
        driver.get(url)
        accept_cookies_if_present(driver)

        while True:
            try:
                button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR,
                                             "a.btn.btn-lg.btn-block.btn-primary.ecomerce-items-scroll-more")))
                button.click()
            except TimeoutException:
                break

        return driver.page_source
    finally:
        driver.quit()


def parse_single_product(product: Tag) -> Product:
    title = product.select_one(".title")["title"]
    description = product.select_one(".description").text
    price = float(product.select_one(".price").text.replace("$", ""))
    rating = int(product.select_one("p[data-rating]")["data-rating"])
    num_of_reviews = int(product.select_one(".review-count").text.split()[0])

    return Product(
        title=title,
        description=description,
        price=price,
        rating=rating,
        num_of_reviews=num_of_reviews
    )


def get_single_page_products(page_soup: Tag) -> List[Product]:
    products = page_soup.select(".card-body")
    return [parse_single_product(product) for product in products]


def get_home_products() -> List[Product]:
    text = requests.get(HOME_URL).text
    soup = BeautifulSoup(text, "html.parser")
    return get_single_page_products(soup)


def get_computers_products() -> List[Product]:
    text = requests.get(COMPUTERS_URL).text
    soup = BeautifulSoup(text, "html.parser")
    return get_single_page_products(soup)


def get_phones_products() -> List[Product]:
    text = requests.get(PHONES_URL).text
    soup = BeautifulSoup(text, "html.parser")
    return get_single_page_products(soup)


def get_laptops_products() -> List[Product]:
    html = get_more_products_html(LAPTOPS_URL)
    soup = BeautifulSoup(html, "html.parser")
    return get_single_page_products(soup)

def get_tablets_products() -> List[Product]:
    html = get_more_products_html(TABLETS_URL)
    soup = BeautifulSoup(html, "html.parser")
    return get_single_page_products(soup)


def get_touch_products() -> List[Product]:
    html = get_more_products_html(TOUCH_URL)
    soup = BeautifulSoup(html, "html.parser")
    return get_single_page_products(soup)


def writer(output_csv_path: str, func) -> None:
    products = func()
    with open(output_csv_path, "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["title", "description", "price", "rating", "num_of_reviews"])
        for product in products:
            writer.writerow(
                [
                    product.title,
                    product.description,
                    product.price,
                    product.rating,
                    product.num_of_reviews
                ]
            )


def get_all_products() -> None:
    writer("home.csv", get_home_products)
    writer("computers.csv", get_computers_products)
    writer("phones.csv", get_phones_products)
    writer("laptops.csv", get_laptops_products)
    writer("tablets.csv", get_tablets_products)
    writer("touch.csv", get_touch_products)


if __name__ == "__main__":
    get_all_products()
