import csv
from dataclasses import dataclass, fields, astuple
import time
from urllib.parse import urljoin

from bs4 import BeautifulSoup, Tag
from selenium import webdriver
from selenium.common import (
    ElementNotInteractableException,
    NoSuchElementException
)
from selenium.webdriver.common.by import By
from selenium.webdriver.ie.webdriver import WebDriver

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")
LAPTOP_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/computers/laptops")
TABLETS_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/computers/tablets")
PHONES_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/phones")
TOUCH_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/phones/touch")
COMPUTERS_USL = urljoin(BASE_URL, "test-sites/e-commerce/more/computers")

names_urls = {
    "home": HOME_URL,
    "laptops": LAPTOP_URL,
    "tablets": TABLETS_URL,
    "phones": PHONES_URL,
    "touch": TOUCH_URL,
    "computers": COMPUTERS_USL,
}


_driver: WebDriver | None = None


def get_driver() -> WebDriver:
    return _driver


def set_driver(new_driver: WebDriver) -> None:
    global _driver
    _driver = new_driver


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
        description=product.select_one(".description").text.replace(
            "\xa0", " "
        ),
        price=float(product.select_one(".price").text.replace("$", "")),
        rating=int(len(product.select("span.ws-icon-star"))),
        num_of_reviews=int(
            product.select_one(".review-count").text.split()[0]
        ),
    )


def get_products(url: str) -> list[Product]:
    driver = get_driver()
    driver.get(url)

    try:
        cookies_btn = driver.find_element(
            By.CSS_SELECTOR, "button.acceptCookies"
        )
        cookies_btn.click()
    except NoSuchElementException:
        pass

    try:
        more_button = driver.find_element(
            By.CLASS_NAME, "ecomerce-items-scroll-more"
        )

        while (
                "display: none" not in more_button.get_attribute("style")
                and more_button.is_displayed()
        ):
            time.sleep(0.1)
            more_button.click()
            more_button = driver.find_element(
                By.CLASS_NAME, "ecomerce-items-scroll-more"
            )
    except (ElementNotInteractableException, NoSuchElementException):
        pass

    text = driver.page_source
    soup = BeautifulSoup(text, "html.parser")
    products = soup.select(".card-body")

    return [parse_single_product(product) for product in products]


def write_product_to_csv(products: list[Product], file_name: str) -> None:
    with open(f"{file_name}.csv", "w") as f:
        write = csv.writer(f)
        write.writerow(PRODUCT_FIELDS)
        write.writerows([astuple(product) for product in products])


def get_all_products() -> None:
    with webdriver.Chrome() as driver:
        set_driver(driver)
        for name, url in names_urls.items():
            write_product_to_csv(get_products(url), name)


if __name__ == "__main__":
    get_all_products()
