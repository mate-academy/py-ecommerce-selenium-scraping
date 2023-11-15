import time
from dataclasses import dataclass, fields, astuple
from urllib.parse import urljoin
import csv

from bs4 import BeautifulSoup, Tag
from selenium import webdriver
from selenium.common import TimeoutException, NoSuchElementException
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

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


def accept_cookies(driver: webdriver) -> None:
    try:
        cookie_btn = driver.find_element(
            By.CLASS_NAME, "acceptCookies"
        )
        cookie_btn.click()
    except NoSuchElementException:
        pass


def more_button(url: str) -> BeautifulSoup:
    driver = webdriver.Chrome()
    driver.get(url)
    accept_cookies(driver)

    try:
        while True:
            more = WebDriverWait(driver, 3).until(
                EC.element_to_be_clickable((By.CLASS_NAME, "ecomerce-items-scroll-more"))
            )

            if not more.is_displayed():
                break

            more.click()

            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "thumbnail"))
            )
    except NoSuchElementException:
        pass
    finally:
        return BeautifulSoup(driver.page_source, "html.parser")


def parse_from_pages(url: str) -> list[Product]:
    soup = more_button(url)
    products_info = soup.select(".thumbnail")
    return [parse_single_product(product) for product in products_info]


def write_products_to_csv(products: [Product], output_csv_path: str) -> None:
    with open(output_csv_path, "w") as file:
        writer = csv.writer(file)
        writer.writerow(PRODUCT_FIELDS)
        for product in products:
            writer.writerow(astuple(product))


def get_all_products() -> None:
    for name, url in URLS.items():
        products = parse_from_pages(url)
        write_products_to_csv(products, f"{name}.csv")


if __name__ == "__main__":
    get_all_products()

