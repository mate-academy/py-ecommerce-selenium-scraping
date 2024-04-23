from typing import List
from urllib.parse import urljoin

from selenium.webdriver.remote.webelement import WebElement
from selenium import webdriver
from selenium.webdriver.common.by import By

from app.web_scraper import accept_cookies, has_scroll_button
from app.product import Product
from app.csv_utils import write_to_csv


BASE_URL = "https://webscraper.io/"
URLS = {
    "home": urljoin(
        BASE_URL, "test-sites/e-commerce/more/"
    ),
    "computers": urljoin(
        BASE_URL, "test-sites/e-commerce/more/computers"
    ),
    "laptops": urljoin(
        BASE_URL, "test-sites/e-commerce/more/computers/laptops"
    ),
    "tablets": urljoin(
        BASE_URL, "test-sites/e-commerce/more/computers/tablets"
    ),
    "phones": urljoin(
        BASE_URL, "test-sites/e-commerce/more/phones"
    ),
    "touch": urljoin(
        BASE_URL, "test-sites/e-commerce/more/phones/touch"
    ),
}


def parse_single_product(product: WebElement) -> Product:
    return Product(
        title=product.find_element(By.CSS_SELECTOR, ".caption > h4 > a")
        .get_attribute("title"),
        description=product.find_element(
            By.CSS_SELECTOR, ".caption > .description"
        ).text,
        price=float(
            product.find_element(By.CSS_SELECTOR, ".caption > .price")
            .text.replace("$", "")
        ),
        rating=len(
            product.find_elements(
                By.CSS_SELECTOR, ".ratings > p:nth-of-type(2) > span"
            )
        ),
        num_of_reviews=int(
            product.find_element(By.CSS_SELECTOR, ".ratings > .review-count")
            .text.replace("reviews", "")
        ),
    )


def get_page_with_products(url: str) -> List[Product]:
    with webdriver.Chrome() as driver:
        driver.get(url)
        accept_cookies(driver)
        has_scroll_button(driver)

        products = driver.find_elements(By.CLASS_NAME, "thumbnail")

        return [
            parse_single_product(product)
            for product in products
        ]


def get_all_products() -> None:
    for key, url in URLS.items():
        products = get_page_with_products(url)
        write_to_csv(f"{key}.csv", products)
