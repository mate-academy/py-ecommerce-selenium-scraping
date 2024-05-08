import time
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By

from app.csv_writer import write_to_csv
from app.product_class import Product


BASE_URL = "https://webscraper.io/"
PAGES_URLS = {
    "home": "test-sites/e-commerce/more/",
    "computers": "test-sites/e-commerce/more/computers/",
    "laptops": "test-sites/e-commerce/more/computers/laptops",
    "tablets": "test-sites/e-commerce/more/computers/tablets",
    "phones": "test-sites/e-commerce/more/phones",
    "touch": "test-sites/e-commerce/more/phones/touch"
}


def get_options() -> Options:
    options = Options()
    options.add_argument("--headless=new")
    return options


def accept_cookies(driver: WebDriver) -> None:
    driver.find_element(By.CLASS_NAME, "acceptCookies").click()


def load_more_elements_for_page(driver: WebDriver) -> str:
    more_link = driver.find_element(
        By.CLASS_NAME, "ecomerce-items-scroll-more"
    )

    while more_link.is_displayed():
        ActionChains(
            driver
        ).move_to_element(more_link).click(more_link).perform()
        time.sleep(1)

    return driver.page_source


def get_single_product(product: BeautifulSoup) -> Product:
    return Product(
        title=product.select_one(".title")["title"],
        description=product.select_one(".description").text.replace(" ", " "),
        price=float(product.select_one(".price").text.replace("$", "")),
        rating=len(product.select(".ratings > p > span")),
        num_of_reviews=int(
            product.select_one(".ratings > p.review-count").text[:-8]
        )
    )


def load_full_page(link_: str, driver: WebDriver) -> BeautifulSoup:
    driver.get(link_)
    accept_cookies(driver)
    soup = BeautifulSoup(
        load_more_elements_for_page(driver),
        "html.parser"
    )
    return soup


def get_single_page_products(page_name: str, driver: WebDriver) -> None:
    link_ = urljoin(BASE_URL, PAGES_URLS[page_name])
    page = requests.get(link_).content
    soup = BeautifulSoup(page, "html.parser")

    if soup.select_one(".ecomerce-items-more"):
        soup = load_full_page(link_, driver)

    products = soup.select(".thumbnail")

    parsed_data = [get_single_product(product) for product in products]

    filename = page_name + ".csv"
    write_to_csv(filename, parsed_data)


def get_all_products() -> None:
    with webdriver.Chrome(options=get_options()) as driver:
        for page in PAGES_URLS:
            get_single_page_products(page, driver)


if __name__ == "__main__":
    get_all_products()
