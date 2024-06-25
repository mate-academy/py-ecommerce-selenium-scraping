import csv
import time

from selenium import webdriver
from selenium.common import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.chrome.options import Options
from dataclasses import dataclass, asdict
from urllib.parse import urljoin

BASE_URL = "https://webscraper.io/test-sites/e-commerce/more/"

PAGES = {
    "home": BASE_URL,
    "computers": urljoin(BASE_URL, "computers"),
    "laptops": urljoin(BASE_URL, "computers/laptops"),
    "tablets": urljoin(BASE_URL, "computers/tablets"),
    "phones": urljoin(BASE_URL, "phones"),
    "touch": urljoin(BASE_URL, "phones/touch"),
}


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


class Parser:
    def __init__(self) -> None:
        options = Options()
        options.add_argument("--headless=new")
        self.driver = webdriver.Chrome(options=options)

    def quit(self) -> None:
        self.driver.quit()

    def accept_cookies(self) -> None:
        try:
            self.driver.find_element(By.CLASS_NAME, "acceptCookies").click()
        except NoSuchElementException:
            return

    @staticmethod
    def parse_product(product: WebElement) -> Product:
        title = product.find_element(
            By.CLASS_NAME, "title"
        ).get_attribute("title")
        description = product.find_element(
            By.CLASS_NAME, "description"
        ).text
        price = float(product.find_element(
            By.CLASS_NAME, "price"
        ).text.replace("$", ""))
        rating = len(product.find_elements(
            By.CLASS_NAME, "ws-icon-star"
        ))
        num_of_reviews = int(product.find_element(
            By.CLASS_NAME, "review-count"
        ).text.split()[0])

        return Product(
            title=title,
            description=description,
            price=price,
            rating=rating,
            num_of_reviews=num_of_reviews,
        )

    def parse_products(self, url: str) -> list[Product]:
        self.driver.get(url)
        self.accept_cookies()

        while True:
            try:
                more_button = self.driver.find_element(
                    By.CLASS_NAME, "ecomerce-items-scroll-more"
                )
                time.sleep(0.5)

                if more_button.value_of_css_property("display") != "none":
                    more_button.click()
                else:
                    break
            except NoSuchElementException:
                break

        products = self.driver.find_elements(By.CLASS_NAME, "product-wrapper")

        return [self.parse_product(product) for product in products]

    @staticmethod
    def write_to_css(products: list[Product], filename: str) -> None:
        with open(f"{filename}.csv", "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)

            writer.writerow(
                ["title", "description", "price", "rating", "num_of_reviews"]
            )

            for product in products:
                writer.writerow([value for value in asdict(product).values()])


def get_all_products() -> None:
    parser = Parser()

    for page, url in PAGES.items():
        parser.write_to_css(parser.parse_products(url), page)

    parser.quit()


if __name__ == "__main__":
    get_all_products()
