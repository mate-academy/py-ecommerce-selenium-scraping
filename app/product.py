import time
from tqdm import tqdm

from dataclasses import dataclass, fields
from urllib.parse import urljoin

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as ec

from .settings import BASE_URL, SCROLL_PAUSE_TIME
from .web_driver import WebDriverSingleton


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


PRODUCT_FIELDS = [field.name for field in fields(Product)]

# Product CSS selectors to which we are going to navigate
TITLE = ".caption > h4 > a"
DESCRIPTION = ".caption > .card-text"
PRICE = ".caption > .price"
RATING = "div.ratings > p:nth-of-type(2) > span"
NUM_OF_REVIEWS = "div.ratings > p.review-count"

PRODUCTS_CARD = ".card-body"
PAGINATION_BUTTON = ".ecomerce-items-scroll-more"


class ProductParser:
    """ Class for Parsing web app webscraper.io"""
    def __init__(self, page_url: str):
        self.page_url = urljoin(BASE_URL, page_url)
        self.driver = self.get_selenium_page()

    def get_selenium_page(self) -> webdriver.Chrome:
        """ Get webdriver and GET page using self.page_url """
        driver = WebDriverSingleton.get_driver()
        driver.get(self.page_url)
        # let page to fully load
        time.sleep(SCROLL_PAUSE_TIME)

        return driver

    def create_product(self, product_body: WebElement) -> Product:
        return Product(
            title=product_body.find_element(
                By.CSS_SELECTOR, TITLE
            ).get_attribute("title"),
            description=product_body.find_element(
                By.CSS_SELECTOR, DESCRIPTION
            ).text,
            price=float(product_body.find_element(
                By.CSS_SELECTOR, PRICE
            ).text.replace("$", "")),
            rating=len(product_body.find_elements(By.CSS_SELECTOR, RATING)),
            num_of_reviews=int(
                product_body.find_element(
                    By.CSS_SELECTOR, NUM_OF_REVIEWS
                ).text.split(" ")[0]
            )
        )

    def has_pagination(self) -> bool:
        """ Check if pagination button exist and displayed """
        try:
            pagination_button = self.driver.find_element(
                By.CSS_SELECTOR, PAGINATION_BUTTON
            )
            return pagination_button.is_displayed()
        except ec.NoSuchElementException:
            return False

    def more_products(self) -> None:
        """ Update the self.page_soup with more products from pagination """
        while self.has_pagination():
            # self.scroll_page_from_button(900)

            more_products = self.driver.find_element(
                By.CLASS_NAME, PAGINATION_BUTTON[1:]
            )
            # click pagination button
            more_products.click()
            time.sleep(SCROLL_PAUSE_TIME)

    def get_all_products(self) -> list[Product]:
        """ Return page products """
        self.more_products()
        products = self.driver.find_elements(
            By.CSS_SELECTOR, PRODUCTS_CARD
        )

        return [
            self.create_product(product)
            for product in tqdm(products)
        ]
