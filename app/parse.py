import csv
import datetime
import time
from dataclasses import dataclass, fields, astuple
from urllib.parse import urljoin

from bs4 import BeautifulSoup, Tag
from selenium import webdriver
from selenium.common import NoSuchElementException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement

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


def parse_single_product(product: Tag) -> Product:
    return Product(
        title=product.select_one(".title")["title"],
        description=(
            product.select_one(".description").text.replace(u'\xa0', u' ')
        ),
        price=float(product.select_one(".price").text[1:]),
        rating=len(product.select(".glyphicon-star")),
        num_of_reviews=int(product.select_one(".ratings").text.split()[0]),
    )


def parse_page(url: str, driver: WebDriver) -> list[Product]:
    driver.get(url)
    scroll_button = None

    try:
        driver.find_element(By.CLASS_NAME, "acceptCookies").click()
    except NoSuchElementException:
        pass

    try:
        scroll_button = driver.find_element(
            By.CLASS_NAME, "ecomerce-items-scroll-more"
        )
    except NoSuchElementException:
        pass

    if scroll_button is not None:
        while scroll_button.is_displayed():
            scroll_button.click()
            time.sleep(0.1)

    page = driver.page_source
    soup = BeautifulSoup(page, "html.parser")
    products = soup.select(".thumbnail")
    return [
        parse_single_product(product)
        for product in products
    ]


def write_csv_file(file_name: str, products: list[Product]) -> None:
    with open(file_name, "w") as file:
        csv_file = csv.writer(file)
        csv_file.writerow([field.name for field in fields(Product)])
        csv_file.writerows([astuple(quote) for quote in products])


def get_all_products() -> None:
    chrome_options = Options()
    chrome_options.add_argument('--headless')

    with webdriver.Chrome(options=chrome_options) as driver:
        for name, url in URLS.items():
            products = parse_page(url, driver)
            write_csv_file(f"{name}.csv", products)


if __name__ == "__main__":
    get_all_products()
