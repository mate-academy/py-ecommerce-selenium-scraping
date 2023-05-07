import csv
from dataclasses import dataclass, fields, astuple
import time
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common import NoSuchElementException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")
URLS = {
    "home": HOME_URL,
    "computers": urljoin(HOME_URL, "computers"),
    "laptops": urljoin(HOME_URL, "computers/laptops"),
    "tablets": urljoin(HOME_URL, "computers/tablets"),
    "phones": urljoin(HOME_URL, "phones"),
    "touch": urljoin(HOME_URL, "phones/touch")
}


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


def parse_single_product(product_soup: BeautifulSoup) -> Product:
    return Product(
        title=product_soup.select_one(".title")["title"],
        description=product_soup.select_one(".description").text,
        price=float(product_soup.select_one(".price").text.replace("$", "")),
        rating=len(product_soup.select(".glyphicon")),
        num_of_reviews=int(product_soup.select_one(".ratings").text.split()[0])
    )


def click_more_button(url: str, driver: WebDriver) -> list[Product]:
    driver.get(url)
    scroll_button = None

    try:
        driver.find_element(By.CLASS_NAME, "acceptCookies").click()
    except NoSuchElementException:
        pass

    try:
        scroll_button = driver.find_element(
            By.CLASS_NAME,
            "ecomerce-items-scroll-more"
        )
    except NoSuchElementException:
        pass

    if scroll_button is not None:
        while scroll_button.is_displayed():
            scroll_button.click()
            time.sleep(1)

    soup = BeautifulSoup(driver.page_source, "html.parser")
    products = soup.select(".thumbnail")
    return [parse_single_product(product) for product in products]


def csv_file_create(file_name: str, products: list[Product]) -> None:
    with open(file_name, "w") as file:
        csv_file = csv.writer(file)
        csv_file.writerow([field.name for field in fields(Product)])
        csv_file.writerow([astuple(product) for product in products])


def get_all_products() -> None:
    options = Options()

    with webdriver.Chrome(options=options) as driver:
        for file_name, url in URLS.items():
            products = click_more_button(url, driver)
            csv_file_create(f"{file_name}.csv", products)


if __name__ == "__main__":
    get_all_products()
