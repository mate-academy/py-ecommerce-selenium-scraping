import csv
import logging
import sys
import time
from dataclasses import astuple, dataclass, fields
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup, Tag
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")


class LoggerFactory:
    _LOG = None

    @staticmethod
    def __create_logger(log_file: str, log_level: str) -> logging.Logger:
        """
        A private method that interacts with the python
        logging module
        """
        # set the logging format
        log_format = "[%(levelname)5s]:  %(message)s"

        # Initialize the class variable with logger object
        LoggerFactory._LOG = logging.getLogger(log_file)
        logging.basicConfig(
            level=logging.INFO,
            format=log_format,
            handlers=[logging.StreamHandler(sys.stdout)],
        )

        # set the logging level based on the user selection
        log_level = log_level.upper()
        if log_level in {"INFO", "ERROR", "DEBUG"}:
            LoggerFactory._LOG.setLevel(getattr(logging, log_level))

        return LoggerFactory._LOG

    @staticmethod
    def get_logger(log_file: str, log_level: str) -> logging.Logger:
        """
        A static method called by other modules to initialize logger in
        their own module
        """
        logger = LoggerFactory.__create_logger(log_file, log_level)

        # return the logger object
        return logger


logger = LoggerFactory.get_logger("mymodule.py", log_level="INFO")


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


PRODUCT_FIELDS = [field.name for field in fields(Product)]


class Parser:
    def __init__(self, driver: WebDriver, url_to_parse: str) -> None:
        self.driver = driver
        self.url_to_parse = url_to_parse
        self.navigation_data_cache = None
        self._initialize_navigation_cache()

    def _initialize_navigation_cache(self) -> None:
        if self.navigation_data_cache is None:
            self.driver.get(self.url_to_parse)

            self.click_accept_cookies()

            nav = self.driver.find_element(By.ID, "side-menu")
            nav_items = nav.find_elements(By.TAG_NAME, "a")
            navigation_data = {}

            for nav_item in nav_items:
                class_attr = nav_item.get_attribute("class").strip()
                if class_attr == "category-link":
                    nav_item_href = nav_item.get_attribute("href")
                    navigation_data[nav_item.text] = nav_item.get_attribute("href")
                    self.driver.get(nav_item_href)
                    sub_nav_items = self.driver.find_elements(
                        By.CLASS_NAME, "subcategory-link "
                    )

                    for sub_nav_item in sub_nav_items:
                        navigation_data[sub_nav_item.text] = sub_nav_item.get_attribute(
                            "href"
                        )
                    self.driver.back()

                else:
                    navigation_data[nav_item.text] = nav_item.get_attribute("href")
            logger.info("Analyzed navigation section")
            self.navigation_data_cache = navigation_data

    @property
    def get_pages_from_navigation(self) -> dict[str, str]:
        return self.navigation_data_cache

    @staticmethod
    def get_url_soup(page_url: str) -> BeautifulSoup:
        response = requests.get(page_url).content
        return BeautifulSoup(response, "html.parser")

    def click_accept_cookies(self) -> None:
        cookies_btn = self.driver.find_element(By.CLASS_NAME, "acceptCookies")
        cookies_btn.click()
        logger.info("ACCEPTED COOKIES")

    def click_more_button(self, page_url: str) -> None:
        self.driver.get(page_url)

        while True:
            more_button = self.driver.find_element(
                By.CLASS_NAME, "ecomerce-items-scroll-more"
            )
            if more_button.get_attribute("style") == "display: none;":
                break
            self.driver.execute_script("arguments[0].click();", more_button)
            time.sleep(0.1)

    @staticmethod
    def parse_single_product(product_soup: Tag) -> Product:
        return Product(
            title=product_soup.select_one(".title")["title"],
            description=product_soup.select_one(".description").text.replace(
                "\xa0", " "
            ),
            price=float(product_soup.select_one("h4.price").text.replace("$", "")),
            rating=len(product_soup.select(".ratings > p > span")),
            num_of_reviews=int(product_soup.select_one(".ratings > p").text.split()[0]),
        )

    def get_single_page_products(self, page_url: str) -> list[Product]:
        logging.info(f"Parsing page: {page_url}")
        self.driver.get(page_url)
        more_button_elements = self.driver.find_elements(
            By.CLASS_NAME, "ecomerce-items-scroll-more"
        )

        if more_button_elements:
            logging.info("FOUND MORE BTN")
            self.click_more_button(page_url)

        page_soup = BeautifulSoup(self.driver.page_source, "html.parser")
        products_soup = page_soup.select(".thumbnail")

        return [
            self.parse_single_product(product_soup) for product_soup in products_soup
        ]

    @staticmethod
    def write_data_to_csv(product_name: str, products: list[Product]) -> None:
        with open(f"{product_name}.csv", "w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(PRODUCT_FIELDS)
            writer.writerows([astuple(product) for product in products])


def get_all_products() -> None:
    with webdriver.Chrome() as new_driver:
        parser = Parser(new_driver, HOME_URL)
        for product_name, product_link in parser.get_pages_from_navigation.items():
            products = parser.get_single_page_products(product_link)
            parser.write_data_to_csv(product_name, products)


if __name__ == "__main__":
    get_all_products()
