import csv
import logging
import sys

from dataclasses import dataclass, fields, astuple
from urllib.parse import urljoin
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException

from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")
PRODUCTS_PAGES = {
    "home": HOME_URL,
    "computers": urljoin(HOME_URL, "computers"),
    "laptops": urljoin(HOME_URL, "computers/laptops"),
    "tablets": urljoin(HOME_URL, "computers/tablets"),
    "phones": urljoin(HOME_URL, "phones"),
    "touch": urljoin(HOME_URL, "phones/touch"),
}


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int

    @classmethod
    def parse_single_product(cls, product_soup: BeautifulSoup) -> "Product":
        return cls(
            title=product_soup.select_one(".title")["title"],
            description=product_soup.select_one(
                ".description"
            ).text.strip().replace("\xa0", " "),
            price=float(product_soup.select_one(".price").text.strip("$")),
            rating=len(
                product_soup.find_all("span", class_="ws-icon ws-icon-star")
            ),
            num_of_reviews=int(
                product_soup.select_one(
                    "div.ratings > p.review-count"
                ).text.split()[0]
            ),
        )


class ProductParser:
    def __init__(self, driver: webdriver.Chrome) -> None:
        self.driver = driver

    def load_more(self) -> None:
        while True:
            try:
                button = self.driver.find_element(
                    By.CLASS_NAME, "ecomerce-items-scroll-more"
                )
                if button.is_displayed():
                    ActionChains(self.driver).click(button).perform()
                else:
                    break
            except NoSuchElementException:
                break

    def accept_cookies(self) -> None:
        try:
            accept_cookies_button = self.driver.find_element(
                By.CLASS_NAME, "acceptContainer"
            )
            accept_cookies_button.click()
            logging.info("Cookie banner accepted")
        except NoSuchElementException:
            logging.info("Cookies banner not found")

    def get_page_products(self, url: str) -> [Product]:
        self.driver.get(url)
        self.accept_cookies()
        self.load_more()
        soup = BeautifulSoup(self.driver.page_source, "html.parser")
        return [
            self.parse_single_product(product)
            for product in soup.select(".thumbnail")
        ]

    @staticmethod
    def parse_single_product(product_soup: BeautifulSoup) -> Product:
        return Product(
            title=product_soup.select_one(".title")["title"],
            description=product_soup.select_one(
                ".description"
            ).text.strip().replace("\xa0", " "),
            price=float(product_soup.select_one(".price").text.strip("$")),
            rating=len(
                product_soup.find_all("span", class_="ws-icon ws-icon-star")
            ),
            num_of_reviews=int(
                product_soup.select_one(
                    "div.ratings > p.review-count"
                ).text.split()[0]
            ),
        )

    @staticmethod
    def write_products_to_csv(file_name: str, products: [Product]) -> None:
        with open(file_name, "w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow([field.name for field in fields(Product)])
            writer.writerows([astuple(product) for product in products])
        logging.info(f"Products saved to {file_name}")


def get_all_products() -> None:
    with webdriver.Chrome() as driver:
        parser = ProductParser(driver)
        for page_name, url in PRODUCTS_PAGES.items():
            logging.info(f"Start parsing {page_name} page")
            products = parser.get_page_products(url)
            ProductParser.write_products_to_csv(f"{page_name}.csv", products)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="[%(levelname)8s]: %(message)s",
        handlers=[
            logging.FileHandler("parser.log"),
            logging.StreamHandler(sys.stdout),
        ],
    )
    get_all_products()
