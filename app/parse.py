from time import sleep
from tqdm import tqdm

from selenium import webdriver
from selenium.common import NoSuchElementException
from selenium.common.exceptions import ElementNotInteractableException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from urllib.parse import urljoin

from app.storage import Product, csv_writer

BASE_URL = "https://webscraper.io/"

URLS_TO_SCRAPE = {
    "home": "test-sites/e-commerce/more/",
    "computers": "test-sites/e-commerce/more/computers",
    "laptops": "test-sites/e-commerce/more/computers/laptops",
    "tablets": "test-sites/e-commerce/more/computers/tablets",
    "phones": "test-sites/e-commerce/more/phones",
    "touch": "test-sites/e-commerce/more/phones/touch",
}


class EcommerceScraper:
    def __init__(self) -> None:
        self.options = Options()
        self.driver = webdriver.Chrome(options=self.modify_options())

    def modify_options(self) -> Options:
        self.options.add_argument("--headless=new")
        return self.options

    def accept_cookies(self) -> None:
        try:
            accept_cookies = self.driver.find_element(
                By.CLASS_NAME, "acceptCookies"
            )
            accept_cookies.click()
        except NoSuchElementException:
            print("No need to accept cookies. No actions taken.")

    def has_more(self) -> bool:
        try:
            pagination = self.driver.find_element(
                By.CLASS_NAME, "ecomerce-items-scroll-more"
            )
            return pagination.is_displayed()
        except NoSuchElementException:
            return False

    def extract_all_products(self) -> None:
        while self.has_more():
            try:
                more = self.driver.find_element(
                    By.CLASS_NAME, "ecomerce-items-scroll-more"
                )
                more.click()
            except ElementNotInteractableException:
                sleep(0.15)

    @staticmethod
    def parse_single_product(card: WebElement) -> Product:
        title = card.find_element(
            By.CSS_SELECTOR, ".caption > h4 > a"
        ).get_attribute("title")

        description = card.find_element(
            By.CSS_SELECTOR, ".caption > .description"
        ).text

        price = float(
            card.find_element(
                By.CSS_SELECTOR, ".caption > .price"
            ).text[1:]
        )

        rating = len(
            card.find_elements(
                By.CSS_SELECTOR, ".ratings > p > span[class^='ws-icon']"
            )
        )

        num_of_reviews = int(
            card.find_element(
                By.CSS_SELECTOR, ".ratings > .review-count"
            ).text.split()[0]
        )

        return Product(
            title=title,
            description=description,
            price=price,
            rating=rating,
            num_of_reviews=num_of_reviews,
        )

    def scrape_all_products(self, url_to_parse: str) -> list[Product]:
        self.driver.get(url_to_parse)
        self.accept_cookies()
        self.extract_all_products()

        product_cards = self.driver.find_elements(By.CLASS_NAME, "thumbnail")

        return [
            self.parse_single_product(product_card)
            for product_card in product_cards
        ]


def get_all_products() -> None:
    scraper = EcommerceScraper()

    for page_name, url in tqdm(
            URLS_TO_SCRAPE.items(),
            desc="Total progress",
            position=0,
            leave=True
    ):
        products = scraper.scrape_all_products(urljoin(BASE_URL, url))
        csv_writer(page_name, products)


if __name__ == "__main__":
    get_all_products()
