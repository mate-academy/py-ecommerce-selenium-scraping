import csv
from dataclasses import dataclass, fields, astuple
from urllib.parse import urljoin

from selenium import webdriver
from selenium.common.exceptions import (
    NoSuchElementException,
    ElementNotInteractableException
)
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

from tqdm import tqdm

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more")


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


PRODUCT_FIELDS = [field.name for field in fields(Product)]

_driver: WebDriver | None = None


def get_driver() -> WebDriver:
    return _driver


def set_driver(new_driver: WebDriver) -> None:
    global _driver
    _driver = new_driver


def get_all_products() -> None:
    addresses = {
        "home": "/",
        "computers": "/computers",
        "laptops": "/computers/laptops",
        "tablets": "/computers/tablets",
        "phones": "/phones",
        "touch": "/phones/touch"
    }
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    with webdriver.Chrome(options=chrome_options) as new_driver:
        for name, address in addresses.items():
            set_driver(new_driver)
            driver = get_driver()
            driver.get(HOME_URL + address)
            if name == "home":
                accept_cookies(driver)
            press_more(driver)
            product = parse_products(driver)
            write_product_to_csv_path(name, product)


def accept_cookies(driver: WebDriver) -> None:
    accept_container = driver.find_element(By.ID, "cookieBanner")
    cookie_access = accept_container.find_element(
        By.CLASS_NAME,
        "acceptCookies"
    )
    cookie_access.click()


def press_more(driver: WebDriver) -> None:
    btn_section = driver.find_element(By.CLASS_NAME, "col-lg-9")
    try:
        more_btn = (
            btn_section.find_element(
                By.CLASS_NAME,
                "ecomerce-items-scroll-more"
            )
        )
        while more_btn:
            more_btn.click()
    except NoSuchElementException:
        pass
    except ElementNotInteractableException:
        pass


def parse_products(driver: WebDriver) -> list[Product]:
    card_bodies = driver.find_elements(By.CLASS_NAME, "card-body")
    list_of_products = []
    for card_body in tqdm(card_bodies):
        list_of_products.append(Product(
            title=(card_body.find_element(By.CLASS_NAME, "title")
                   .get_attribute("title")),
            description=(card_body.find_element(By.CLASS_NAME, "description")
                         .text),
            price=(float(card_body.find_element(By.CLASS_NAME, "price")
                         .text.replace("$", ""))),
            rating=(
                len(
                    card_body.find_elements(
                        By.CLASS_NAME,
                        "ws-icon.ws-icon-star"
                    )
                )
            ),
            num_of_reviews=(
                int(
                    card_body.find_element(
                        By.CLASS_NAME,
                        "review-count"
                    ).text.split()[0]
                )
            )
        )
        )
    return list_of_products


def write_product_to_csv_path(name: str, products: [Product]) -> None:
    with open(name + ".csv", "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(PRODUCT_FIELDS)
        writer.writerows([astuple(product) for product in products])


if __name__ == "__main__":
    get_all_products()
