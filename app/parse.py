import csv
import time
from copy import deepcopy
from dataclasses import dataclass, fields, asdict
from typing import List, Dict
from urllib.parse import urljoin
from selenium.common import NoSuchElementException
from tqdm import tqdm
from selenium import webdriver
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int

    @staticmethod
    def product_fields() -> list:
        return [field.name for field in fields(Product)]


class SeleniumDriver:
    _driver: WebDriver | None = None

    @classmethod
    def get_driver(cls) -> WebDriver:
        return cls._driver

    @classmethod
    def set_driver(cls, new_driver: WebDriver) -> None:
        cls._driver = new_driver


class ProductScraper:

    def __init__(self) -> None:
        self.driver = SeleniumDriver.get_driver()

    @staticmethod
    def write_products_to_csv(name: str, products: List[Product]) -> None:
        with open(
            name.lower() + ".csv", "w", encoding="utf-8", newline=""
        ) as file:
            writer = csv.DictWriter(file, fieldnames=Product.product_fields())

            writer.writeheader()

            for product in products:
                writer.writerow(asdict(product))

    def click_more(self) -> None:
        try:
            more = self.driver.find_element(By.CLASS_NAME, "btn-primary")
        except NoSuchElementException:
            more = None
        if more:
            attribute = more.get_attribute("style")
            while attribute != "display: none;":
                more.click()
                time.sleep(0.25)
                attribute = more.get_attribute("style")

    def parse_one_page(self, url: str) -> List[Product]:
        list_products = []
        self.driver.get(url)

        self.click_more()

        products = self.driver.find_elements(By.CLASS_NAME, "thumbnail")
        for product in tqdm(products):
            list_products.append(
                Product(
                    title=product.find_element(
                        By.CLASS_NAME, "title"
                    ).get_attribute("title"),
                    description=product.find_element(
                        By.CLASS_NAME, "description"
                    ).text,
                    price=float(
                        product.find_element(
                            By.CLASS_NAME, "price"
                        ).text.replace("$", "")
                    ),
                    rating=len(
                        product.find_elements(By.CLASS_NAME, "ws-icon-star")
                    ),
                    num_of_reviews=int(
                        product.find_element(
                            By.CLASS_NAME, "review-count"
                        ).text.split()[0]
                    ),
                ),
            )
        return list_products

    def get_sub_categories_urls(self, url: str) -> Dict[str, str] | None:
        self.driver.get(url)
        try:
            self.driver.find_element(By.TAG_NAME, "i")
            sub_categories = self.driver.find_elements(
                By.CLASS_NAME, "subcategory-link"
            )
            return {
                url.text: url.get_attribute("href") for url in sub_categories
            }
        except NoSuchElementException:
            return None

    def get_all_urls(self) -> dict:
        dict_urls = {}
        page = urljoin(BASE_URL, HOME_URL)
        self.driver.get(page)

        try:
            self.driver.find_element(By.CLASS_NAME, "acceptCookies").click()
        except NoSuchElementException:
            print("Accept Cookies not found")

        nav_block = self.driver.find_element(By.ID, "side-menu").find_elements(
            By.CLASS_NAME, "nav-item "
        )
        for url in tqdm(nav_block):
            navigation_item = url.find_element(By.TAG_NAME, "a")
            dict_urls[navigation_item.text] = navigation_item.get_attribute(
                "href"
            )
        for url in deepcopy(dict_urls).values():
            sub = self.get_sub_categories_urls(url)
            if sub:
                dict_urls.update(sub)

        return dict_urls


def get_all_products() -> None:
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    with webdriver.Chrome(options=chrome_options) as new_driver:
        SeleniumDriver.set_driver(new_driver)
        driver = ProductScraper()

        list_of_pages = driver.get_all_urls()
        for name, url in list_of_pages.items():
            print(f"Start: {name}")
            list_products = driver.parse_one_page(url)

            ProductScraper.write_products_to_csv(name, list_products)


if __name__ == "__main__":
    get_all_products()
