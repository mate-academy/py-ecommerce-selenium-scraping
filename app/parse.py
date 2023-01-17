import csv
import logging
import sys
import time
from dataclasses import dataclass, fields, astuple
from urllib.parse import urljoin
from selenium import webdriver
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup, Tag

BASE_URL = "https://webscraper.io"
URLS_TO_PARSE = {
    "home": "/test-sites/e-commerce/more",
    "computers": "/test-sites/e-commerce/more/computers",
    "laptops": "/test-sites/e-commerce/more/computers/laptops",
    "tablets": "/test-sites/e-commerce/more/computers/tablets",
    "phones": "/test-sites/e-commerce/more/phones",
    "touch": "/test-sites/e-commerce/more/phones/touch",
}

logging.basicConfig(
    level=logging.INFO,
    format="--> %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int
    additional_info: dict[str, float]


class Parser:
    def __init__(self):
        self.driver = webdriver.Chrome()
        self.driver.get(BASE_URL)
        self.accept_cookies()

    def close(self):
        self.driver.close()

    def accept_cookies(self):
        logging.info("waiting for cookies bar")
        time.sleep(0.1)
        cookies_button = self.driver.find_elements(
            By.CLASS_NAME, "acceptCookies"
        )
        if cookies_button:
            logging.info("there is cookies bar")
            cookies_button[0].click()
        else:
            logging.info("there is NO cookies bar")

    def parse_single_product_prices(self, product_url: str) -> dict:
        self.driver.get(urljoin(BASE_URL, product_url))
        swatches = self.driver.find_elements(By.CLASS_NAME, "swatches")
        prises = {}
        if swatches:
            buttons = swatches[0].find_elements(By.TAG_NAME, "button")
            for button in buttons:
                if not button.get_property("disabled"):
                    button.click()
                    prises[
                        button.get_property("value")
                    ] = float(self.driver.find_element(
                        By.CLASS_NAME, "price"
                    ).text.replace("$", ""))
        return prises

    def parse_single_product(self, product_soup: Tag) -> Product:
        return Product(
            title=product_soup.select_one(".title")["title"],
            price=float(
                product_soup.select_one(".price").text.replace("$", "")
            ),
            description=product_soup.select_one(
                ".description"
            ).text.replace(" ", " "),
            rating=len(product_soup.select(".glyphicon")),
            num_of_reviews=int(
                product_soup.select_one(
                    ".ratings > p.pull-right"
                ).text.split()[0]
            ),
            additional_info=self.parse_single_product_prices(
                product_soup.select_one(".title")["href"]
            ),
        )

    def scroll_for_all_products(self):
        scroll_button = self.driver.find_elements(
            By.CLASS_NAME, "ecomerce-items-scroll-more"
        )
        scroll_number_counter = 0
        if scroll_button:
            logging.info("start page scrolling")
            while not scroll_button[0].get_property("style"):
                scroll_number_counter += 1
                logging.info(
                    f"scroll button is active - click({scroll_number_counter})"
                )
                scroll_button[0].click()
                time.sleep(0.1)

    def get_products_from_tab(self, url_to_parse):
        logging.info(f"getting data from {url_to_parse}")
        self.driver.get(urljoin(BASE_URL, url_to_parse))
        logging.info(f"get data from {url_to_parse}")
        self.scroll_for_all_products()

        page_source = self.driver.page_source
        page_soup = BeautifulSoup(page_source, 'html.parser')
        products_soup = page_soup.select(".thumbnail")

        all_products = []
        for product_soup in products_soup:
            all_products.append(self.parse_single_product(product_soup))
        return all_products

    @staticmethod
    def wright_products_to_csv(source, products):
        with open(
                file=f"{source}.csv",
                mode="w",
                encoding="utf-8",
                newline=""
        ) as scv_data:
            object_writer = csv.writer(scv_data)
            object_writer.writerow([field.name for field in fields(Product)])
            object_writer.writerows([astuple(product) for product in products])

    def get_all_products(self):
        for source, url in URLS_TO_PARSE.items():
            products = self.get_products_from_tab(url)
            self.wright_products_to_csv(source, products)


if __name__ == "__main__":
    parser = Parser()
    parser.get_all_products()
