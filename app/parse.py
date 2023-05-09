import csv
import time
from dataclasses import dataclass
from typing import List
from urllib.parse import urljoin

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By


BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")
MORE = "ecomerce-items-scroll-more"
URLS = {
    "home": HOME_URL,
    "computers": urljoin(HOME_URL, "computers"),
    "laptops": urljoin(HOME_URL, "computers/laptops"),
    "tablets": urljoin(HOME_URL, "computers/tablets"),
    "phones": urljoin(HOME_URL, "phones/"),
    "touch": urljoin(HOME_URL, "phones/touch"),
}


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


def get_chrome_driver() -> webdriver.Chrome:
    options = Options()
    options.add_argument("--headless")
    driver = webdriver.Chrome(options=options)
    return driver


def get_products_from_page(driver: webdriver.Chrome) -> List[Product]:
    products = driver.find_elements(By.CLASS_NAME, "thumbnail")
    result_products = []

    for product in products:
        title = product.find_element(By.CLASS_NAME, "title").get_attribute(
            "title"
        )
        description = product.find_element(By.CLASS_NAME, "description").text
        price = float(product.find_element(By.CLASS_NAME, "price").text[1:])
        rating = len(product.find_elements(By.CLASS_NAME, "glyphicon"))
        num_of_reviews = int(
            product.find_element(By.CLASS_NAME, "ratings").text.split()[0]
        )
        result_products.append(
            Product(title, description, price, rating, num_of_reviews)
        )

    return result_products


def write_products_to_file(products: List[Product], filename: str) -> None:
    with open(f"{filename}.csv", "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(
            ["title", "description", "price", "rating", "num_of_reviews"]
        )
        for product in products:
            writer.writerow(product.__dict__.values())


def get_all_products() -> None:
    driver = get_chrome_driver()
    with driver:
        for file_name, url in URLS.items():
            print(f"Parsing data from {url}")
            page = show_more_products(driver, url)
            products = get_products_from_page(page)
            write_products_to_file(products, file_name)


def show_more_products(driver: webdriver, url: str) -> webdriver:
    driver.get(url)
    try:
        cookies = driver.find_element(By.CLASS_NAME, "acceptCookies")
        cookies.click()
    except NoSuchElementException:
        pass

    while True:
        try:
            more_button = driver.find_element(By.CLASS_NAME, MORE)
            if more_button.is_displayed():
                more_button.click()
                time.sleep(0.2)
            else:
                break
        except NoSuchElementException:
            break

    return driver


if __name__ == "__main__":
    get_all_products()
