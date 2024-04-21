import csv
import time
from dataclasses import dataclass, asdict, fields
from typing import List, Union
from urllib.parse import urljoin

from selenium.webdriver.remote.webelement import WebElement
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException

BASE_URL = "https://webscraper.io/"
URLS = {
    "home": urljoin(BASE_URL,
                    "test-sites/e-commerce/more/"),
    "computers": urljoin(BASE_URL,
                         "test-sites/e-commerce/more/computers"),
    "laptops": urljoin(BASE_URL,
                       "test-sites/e-commerce/more/computers/laptops"),
    "tablets": urljoin(BASE_URL,
                       "test-sites/e-commerce/more/computers/tablets"),
    "phones": urljoin(BASE_URL,
                      "test-sites/e-commerce/more/phones"),
    "touch": urljoin(BASE_URL,
                     "test-sites/e-commerce/more/phones/touch"),
}


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


PRODUCT_FIELDS = [field.name for field in fields(Product)]


class WebScraper:
    def __init__(self) -> None:
        self.driver = webdriver.Chrome()

    def __del__(self) -> None:
        self.driver.quit()

    def parse_single_product(self, product: WebElement) -> Product:
        """
        Parse data of a single product.
        """
        return Product(
            title=product.find_element(
                By.CSS_SELECTOR,
                ".caption > h4 > a").get_attribute("title"
                                                   ),
            description=product.find_element(
                By.CSS_SELECTOR,
                ".caption > .description").text,
            price=float(product.find_element(
                By.CSS_SELECTOR,
                ".caption > .price").text.replace("$", "")),
            rating=len(
                product.find_elements(By.CSS_SELECTOR,
                                      ".ratings > p:nth-of-type(2) > span")),
            num_of_reviews=int(
                product.find_element(
                    By.CSS_SELECTOR,
                    ".ratings > .review-count").text.replace("reviews", "")
            )
        )

    def get_page_with_products(self, url: str) -> List[Product]:
        """
        Get the list of products on the page.
        """
        self.driver.get(url)
        self.accept_cookies()
        self.has_scroll_button()
        products = self.driver.find_elements(By.CLASS_NAME, "thumbnail")
        return [self.parse_single_product(product) for product in products]

    def accept_cookies(self) -> None:
        """
        Click on the cookies acceptance button.
        """
        try:
            accept_button = self.driver.find_element(By.CLASS_NAME,
                                                     "acceptCookies")
            accept_button.click()
        except NoSuchElementException:
            pass

    def scroll_page(self) -> None:
        """
        Scroll the page to load more products.
        """
        while True:
            try:
                more_button = self.driver.find_element(
                    By.CSS_SELECTOR,
                    ".ecomerce-items-scroll-more"
                )
                if more_button.is_displayed():
                    more_button.click()
                    time.sleep(1)
                else:
                    break
            except NoSuchElementException:
                break

    def has_scroll_button(self) -> Union[list, bool]:
        """
        Check if the scroll button is present.
        """
        try:
            self.scroll_page()
            time.sleep(1)
        except NoSuchElementException:
            return False

    def write_to_csv(self, file_name: str, products: List[Product]) -> None:
        """
        Write data to a CSV file.
        """
        with open(file_name, "w", encoding="utf-8", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(PRODUCT_FIELDS)
            writer.writerows(
                [asdict(product).values()
                 for product in products]
            )


def get_all_products() -> None:
    """
    Get product data from all URLs and write to CSV files.
    """
    scraper = WebScraper()
    for url_key in URLS:
        products = scraper.get_page_with_products(URLS[url_key])
        scraper.write_to_csv(f"{url_key}.csv", products)


if __name__ == "__main__":
    get_all_products()
