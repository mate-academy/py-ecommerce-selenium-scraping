import time
from dataclasses import dataclass, fields, astuple
from urllib.parse import urljoin
import csv

from bs4 import BeautifulSoup, Tag
from selenium import webdriver
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")
URLS = {
    "home": HOME_URL,
    "phones": urljoin(HOME_URL, "phones/"),
    "touch": urljoin(HOME_URL, "phones/touch"),
    "computers": urljoin(HOME_URL, "computers/"),
    "laptops": urljoin(HOME_URL, "computers/laptops"),
    "tablets": urljoin(HOME_URL, "computers/tablets"),
}


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


PRODUCT_FIELDS = [field.name for field in fields(Product)]


def parse_single_product(product: Tag) -> Product:
    return Product(
        title=product.select_one(".title")["title"],
        description=product.select_one(".description").text.replace("\xa0", " "),
        price=float(product.select_one(".price").text.replace("$", "")),
        rating=len(product.select(".ratings span")),
        num_of_reviews=int(product.select_one(".review-count").text.split()[0])
    )


def get_page_products(page_url: str, driver: WebDriver) -> list[Product]:
    driver.get(page_url)
    cookies = driver.find_elements(By.CLASS_NAME, "acceptCookies")

    if cookies:
        cookies[0].click()

    button_more = driver.find_elements(By.CLASS_NAME, "ecomerce-items-scroll-more")

    if button_more:
        while button_more[0].is_displayed():
            button_more[0].click()
            time.sleep(0.1)

    page = driver.page_source
    page_soup = BeautifulSoup(page, "html.parser")

    products = page_soup.select(".thumbnail")

    return [parse_single_product(product) for product in products]


def write_products_to_csv(products: [Product], output_csv_path: str) -> None:
    with open(output_csv_path, "w") as file:
        writer = csv.writer(file)
        writer.writerow(PRODUCT_FIELDS)
        writer.writerows([astuple(product) for product in products])


def get_all_products() -> None:
    driver = webdriver.Chrome()
    for name, url in URLS.items():
        write_products_to_csv(
            products=get_page_products(url, driver),
            output_csv_path=f"{name}.csv"
        )


if __name__ == "__main__":
    get_all_products()
