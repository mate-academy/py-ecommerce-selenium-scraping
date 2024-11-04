import csv
from dataclasses import dataclass, fields, astuple
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")
COMPUTER_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/computers")
PHONE_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/phones")
LAPTOP_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/computers/laptops")
TABLETS_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/computers/tablets")
TOUCH_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/phones/touch")


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


PRODUCT_FIELDS = [field.name for field in fields(Product)]


def parse_single_product(product_soup: BeautifulSoup) -> Product:
    return Product(
        title=product_soup.select_one(".title")["title"],
        description=product_soup.select_one(
            ".description"
        ).text.replace("\xa0", " "),
        price=float(product_soup.select_one(".price").text.replace("$", "")),
        rating=int(len(product_soup.select("p .ws-icon.ws-icon-star"))),
        num_of_reviews=int(
            product_soup.select_one(
                ".ratings > p.review-count"
            ).text.split()[0]
        ),
    )


def wright_products_to_csv(products: [Product], page: str) -> None:
    with open(f"{page}.csv", "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(PRODUCT_FIELDS)
        writer.writerows([astuple(product) for product in products])


def get_home_product(url: str) -> [Product]:
    page = requests.get(url).content
    soup = BeautifulSoup(page, "html.parser")
    products = soup.select(".thumbnail")
    return [parse_single_product(product_soup) for product_soup in products]


def accept_cookies(driver: webdriver.Chrome) -> None:

    cookies_button = driver.find_element(By.CLASS_NAME, "acceptCookies")
    if cookies_button.is_displayed():
        cookies_button.click()


def get_product_with_pagination(url: str) -> [Product]:
    driver = webdriver.Chrome()
    driver.get(url)
    accept_cookies(driver)

    products = []

    while True:
        try:
            button = driver.find_element(
                By.CLASS_NAME,
                "ecomerce-items-scroll-more"
            )
            button.click()
            driver.implicitly_wait(3)
        except Exception:
            break

    page_source = driver.page_source
    soup = BeautifulSoup(page_source, "html.parser")
    driver.quit()

    products = soup.select(".thumbnail")
    return [parse_single_product(product_soup) for product_soup in products]


def get_all_products() -> None:
    home = get_home_product(HOME_URL)
    computers = get_home_product(COMPUTER_URL)
    phones = get_home_product(PHONE_URL)
    laptops = get_product_with_pagination(LAPTOP_URL)
    tablets = get_product_with_pagination(TABLETS_URL)
    touch = get_product_with_pagination(TOUCH_URL)
    wright_products_to_csv(home, "home")
    wright_products_to_csv(computers, "computers")
    wright_products_to_csv(phones, "phones")
    wright_products_to_csv(laptops, "laptops")
    wright_products_to_csv(tablets, "tablets")
    wright_products_to_csv(touch, "touch")


if __name__ == "__main__":
    get_all_products()
