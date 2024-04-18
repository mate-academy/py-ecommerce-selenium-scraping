import time
from dataclasses import dataclass, fields
from urllib.parse import urljoin

from selenium import webdriver
from selenium.common import NoSuchElementException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from tqdm import tqdm


from app.writer import CSVFileWriter


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


PRODUCT_FIELDS = [field.name for field in fields(Product)]


class WebScraperService:
    BASE_URL = "https://webscraper.io/"

    def __init__(self) -> None:
        self.options = Options()
        self.driver = webdriver.Chrome(options=self._add_options())

    def _add_options(self) -> Options:
        self.options.add_argument("--headless")

        return self.options

    def _update_driver(self, product_url: str) -> None:
        page_url = urljoin(self.BASE_URL, product_url)
        self.driver.get(page_url)

    @staticmethod
    def _parse_single_product(product: WebElement) -> Product:
        return Product(
            title=product.find_element(
                By.CSS_SELECTOR, ".caption > h4 > a"
            ).get_attribute("title"),
            description=product.find_element(
                By.CSS_SELECTOR, ".caption > .card-text"
            ).text,
            price=float(
                product.find_element(
                    By.CSS_SELECTOR, ".caption > .price")
                .text.replace("$", "")
            ),
            rating=len(
                product.find_elements(
                    By.CSS_SELECTOR, "div.ratings > p:nth-of-type(2) > span"
                )
            ),
            num_of_reviews=int(
                product.find_element(
                    By.CSS_SELECTOR, "div.ratings > p.review-count"
                ).text.split(" ")[0]
            ),
        )

    def _accept_cookies(self) -> None:
        try:
            accept_cookies_button = self.driver.find_element(
                By.CLASS_NAME, "acceptCookies"
            )
            accept_cookies_button.click()
        except NoSuchElementException:
            return

    def _has_pagination(self) -> bool:
        try:
            pagination_button = self.driver.find_element(
                By.CSS_SELECTOR, ".ecomerce-items-scroll-more"
            )
            return pagination_button.is_displayed()
        except NoSuchElementException:
            return False

    def _scroll_whole_page(self) -> None:
        while self._has_pagination():
            more_button = self.driver.find_element(
                By.CLASS_NAME, ".ecomerce-items-scroll-more"[1:]
            )
            more_button.click()
            time.sleep(0.2)

    def get_all_products(self, product_url: str) -> list[Product]:
        self._update_driver(product_url)
        self._accept_cookies()
        self._scroll_whole_page()
        products = self.driver.find_elements(By.CSS_SELECTOR, ".card-body")

        return [
            self._parse_single_product(product)
            for product in tqdm(products)
        ]


urls = {
    "home": "/test-sites/e-commerce/more",
    "computers": "/test-sites/e-commerce/more/computers",
    "phones": "/test-sites/e-commerce/more/phones",
    "laptops": "/test-sites/e-commerce/more/computers/laptops",
    "tablets": "/test-sites/e-commerce/more/computers/tablets",
    "touch": "/test-sites/e-commerce/more/phones/touch",
}


def get_all_products() -> None:
    scraper = WebScraperService()
    for file_name, url in urls.items():
        products = scraper.get_all_products(product_url=url)
        file_writer = CSVFileWriter(
            file_name=file_name, column_fields=PRODUCT_FIELDS
        )
        file_writer.write_in_csv_file(data=products)


if __name__ == "__main__":
    get_all_products()
