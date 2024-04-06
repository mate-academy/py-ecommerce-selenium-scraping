import csv

from dataclasses import dataclass, fields, astuple
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.common import (
    NoSuchElementException,
    ElementNotInteractableException,
    ElementClickInterceptedException
)


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


PRODUCT_FIELDS = [product.name for product in fields(Product)]


class ProductParser:
    def __init__(self) -> None:
        self.BASE_URL = "https://webscraper.io/test-sites/e-commerce/more/"
        self.options = Options()
        self.options.add_argument("--headless")
        self.driver = webdriver.Chrome(options=self.options)
        self.driver.get(self.BASE_URL)

    @staticmethod
    def parse_single_product(product: WebElement) -> Product:
        return Product(
            title=product.find_element(
                By.CLASS_NAME, "title"
            ).get_property("title"),
            description=product.find_element(
                By.CLASS_NAME, "description"
            ).text,
            price=float(product.find_element(By.CLASS_NAME, "price").text[1:]),
            rating=len(product.find_elements(By.CLASS_NAME, "ws-icon-star")),
            num_of_reviews=int(product.find_element(
                By.CLASS_NAME, "review-count"
            ).text.split()[0])
        )

    @staticmethod
    def write_data_to_csv(
            data: [Product],
            doc_name: str,
            col_names: list
    ) -> None:
        with open(f"{doc_name}.csv", "w") as file:
            writer = csv.writer(file)
            writer.writerow(col_names)
            writer.writerows([astuple(item) for item in data])

    def click_cookie_button(self) -> None:
        cookie_button = self.driver.find_element(
            By.CLASS_NAME, "acceptCookies"
        )
        cookie_button.click()

    def push_more_button(self) -> None:
        while True:
            try:
                self.driver.find_element(
                    By.CLASS_NAME, "ecomerce-items-scroll-more"
                ).click()
            except (
                    NoSuchElementException,
                    ElementClickInterceptedException,
                    ElementNotInteractableException
            ):
                return

    def get_single_page_products(self) -> list[Product]:
        self.push_more_button()
        products = self.driver.find_elements(By.CLASS_NAME, "thumbnail")

        return [self.parse_single_product(product) for product in products]

    def parse_all_products_from_the_single_page(self, index: int) -> None:
        self.driver.execute_script("window.scrollTo(0, 0)")

        buttons = self.driver.find_elements(
            By.CSS_SELECTOR, ".nav-item > .nav-link"
        )[6:]
        name = buttons[index].text.lower()
        buttons[index].click()

        products = self.get_single_page_products()

        self.write_data_to_csv(products, name, PRODUCT_FIELDS)

    def get_products_from_all_pages(self) -> None:
        page = 0
        buttons = self.driver.find_elements(
            By.CSS_SELECTOR, ".nav-item > .nav-link"
        )[6:]

        while page <= len(buttons) + 1:
            self.parse_all_products_from_the_single_page(page)
            page += 1
        self.parse_all_products_from_the_single_page(-1)


def get_all_products() -> None:
    scraper = ProductParser()
    scraper.click_cookie_button()
    scraper.get_products_from_all_pages()


if __name__ == "__main__":
    get_all_products()
