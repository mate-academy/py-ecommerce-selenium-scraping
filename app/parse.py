import csv
from dataclasses import asdict
from typing import Iterator
from urllib.parse import urljoin

from selenium.common.exceptions import (
    ElementNotInteractableException,
    NoSuchElementException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement

from app.drivers import FirefoxDriver
from app.models import Product

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more")


class ParseProducts(FirefoxDriver):
    @staticmethod
    def _parse_prices(switchers: WebElement) -> Iterator[int]:
        buttons = switchers.find_elements(By.TAG_NAME, "button")
        for button in buttons:
            if not button.get_property("disabled"):
                button.click()
                yield int(button.text)

    def _parse_product(self, card: WebElement) -> Iterator[Product]:
        title = card.find_element(
            By.CSS_SELECTOR, ".caption .title"
        ).get_property("title")
        description = card.find_element(
            By.CSS_SELECTOR, ".caption .description"
        ).text
        ratings = card.find_element(By.CSS_SELECTOR, ".ratings")
        rating = len(ratings.find_elements(By.TAG_NAME, "span"))
        num_of_reviews = int(
            ratings.find_element(By.CSS_SELECTOR, ".review-count").text[:-8]
        )

        try:
            swatches = card.find_element(By.CSS_SELECTOR, ".swatches")
        except NoSuchElementException:
            swatches = None
        prices = (
            self._parse_prices(swatches)
            if swatches
            else [
                float(
                    card.find_element(By.CSS_SELECTOR, ".caption .price").text[
                        1:
                    ]
                )
            ]
        )
        for price in prices:
            yield Product(
                title=title,
                description=description,
                price=price,
                rating=rating,
                num_of_reviews=num_of_reviews,
            )

    def _scroll_more(self) -> None:
        while True:
            try:
                self.driver.find_element(
                    By.CSS_SELECTOR, ".ecomerce-items-scroll-more"
                ).click()
            except (NoSuchElementException, ElementNotInteractableException):
                break

    def _fetch_cards(self, landing_page: str) -> Iterator[WebElement]:
        self.driver.get(landing_page)
        self._scroll_more()
        cards = self.driver.find_elements(By.CSS_SELECTOR, ".card-body")
        if HOME_URL == landing_page:  # Home page.
            product_urls = [
                card.find_element(By.TAG_NAME, "a").get_property("href")
                for card in cards
            ]
            for url in product_urls:
                self.driver.get(url)
                yield self.driver.find_element(By.CSS_SELECTOR, ".card-body")
        else:
            for card in cards:
                yield card

    def _fetch_routes(self, home_page: str = HOME_URL) -> dict[str, str]:
        routes = {}
        self.driver.get(home_page)
        self.driver.find_element(By.CSS_SELECTOR, ".acceptCookies").click()
        a_tags = self.driver.find_elements(
            By.CSS_SELECTOR, ".sidebar-nav .nav-link"
        )
        nav_routes = set(a_tag.get_property("href") for a_tag in a_tags)
        for route in nav_routes:
            self.driver.get(route)
            a_tags = self.driver.find_elements(
                By.CSS_SELECTOR, ".sidebar-nav .nav-link"
            )
            routes.update(
                {
                    a_tag.text.lower(): a_tag.get_property("href")
                    for a_tag in a_tags
                }
            )
        return routes

    @staticmethod
    def _write_csv(fine_name: str, products: list[Product]) -> None:
        with open(f"{fine_name}.csv", "w") as file:
            writer = csv.DictWriter(file, Product.to_field_list())
            writer.writeheader()
            writer.writerows(asdict(product) for product in products)

    def start(self) -> None:
        for page_name, landing_page in self._fetch_routes().items():
            products = [
                product
                for card in self._fetch_cards(landing_page)
                for product in self._parse_product(card)
            ]
            self._write_csv(page_name, products)


def get_all_products() -> None:
    with ParseProducts() as parse:
        parse.start()


if __name__ == "__main__":
    get_all_products()
