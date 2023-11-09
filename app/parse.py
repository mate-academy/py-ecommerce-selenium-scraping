import csv
import time
from dataclasses import dataclass, fields
from urllib.parse import urljoin

import selenium
from selenium import webdriver
from selenium.common import NoSuchElementException
from selenium.webdriver.common.by import By

BASE_URL = "https://webscraper.io/"
webdriver = webdriver.Chrome()
HOME_PAGE = urljoin(BASE_URL, "test-sites/e-commerce/more/")

PAGES = {
    "home": HOME_PAGE,
    "computers": urljoin(BASE_URL, "test-sites/e-commerce/more/computers"),
    "laptops": urljoin(
        BASE_URL, "test-sites/e-commerce/more/computers/laptops"
    ),
    "tablets": urljoin(
        BASE_URL, "test-sites/e-commerce/more/computers/tablets"
    ),
    "phones": urljoin(BASE_URL, "test-sites/e-commerce/more/phones"),
    "touch": urljoin(BASE_URL, "test-sites/e-commerce/more/phones/touch"),
}


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


product_fields = fields(Product)

PRODUCT_HEADERS = [field.name for field in product_fields]


def accept_cookies() -> None:
    cookie_button = webdriver.find_element(By.CLASS_NAME, "acceptCookies")
    cookie_button.click()


def click_more_button() -> None:
    while True:
        try:
            more_button = webdriver.find_element(
                By.CLASS_NAME, "ecomerce-items-scroll-more"
            )
        except NoSuchElementException:
            break
        else:
            if more_button.get_attribute("style"):
                break
            more_button.click()
            time.sleep(0.2)


def get_rating(card: selenium.webdriver) -> int:
    return len(card.find_elements(By.CLASS_NAME, "ws-icon-star"))


def create_product(product_card: selenium.webdriver) -> Product:
    return Product(
        title=product_card.find_element(By.CLASS_NAME, "title").get_attribute(
            "title"
        ),
        description=product_card.find_element(
            By.CLASS_NAME, "description"
        ).text,
        price=float(
            product_card.find_element(By.CLASS_NAME, "price").text.replace(
                "$", ""
            )
        ),
        rating=get_rating(product_card),
        num_of_reviews=int(
            product_card.find_element(
                By.CLASS_NAME, "review-count"
            ).text.split(" ")[0]
        ),
    )


def get_products_from_page(page: str) -> list:
    list_of_products = []
    webdriver.get(page)
    click_more_button()
    cards = webdriver.find_elements(By.CLASS_NAME, "thumbnail")
    for card in cards:
        list_of_products.append(create_product(card))

    return list_of_products


def write_page_content(file_path: str, products: list[Product]) -> None:
    data = [
        [
            product.title,
            product.description,
            product.price,
            product.rating,
            product.num_of_reviews,
        ]
        for product in products
    ]

    with open(file_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(PRODUCT_HEADERS)
        writer.writerows(data)


def get_all_products() -> None:
    webdriver.get(HOME_PAGE)
    accept_cookies()
    for file_name, page in PAGES.items():
        products = get_products_from_page(page)
        write_page_content(f"{file_name}.csv", products)
    webdriver.quit()


if __name__ == "__main__":
    get_all_products()
