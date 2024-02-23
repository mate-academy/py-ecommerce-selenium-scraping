import csv

from dataclasses import astuple

from bs4 import BeautifulSoup, Tag
from selenium import webdriver


from app.config import PAGES_TO_PARSE_WITH_SAVE_PATH
from app.models import Product, PRODUCT_FIELDS
from app.web_driver import (
    click_button_many_times,
    get_driver, set_driver,
    check_cookies
)


class Scrapper:

    @staticmethod
    def parse_single_product(product_soup: Tag) -> Product:
        return Product(
            title=product_soup.select_one(".title")["title"],
            description=product_soup.select_one(".description")
            .text.replace(" ", " "),
            price=float(
                product_soup.select_one(".price")
                .text.replace("$", "")
            ),
            rating=len(product_soup.select(".ws-icon-star")),
            num_of_reviews=int(
                product_soup.select_one(".review-count").text.split()[0]
            )
        )

    def get_single_page_products(
            self, page_soup: BeautifulSoup
    ) -> list[Product]:
        products = page_soup.select(".thumbnail")

        return [
            self.parse_single_product(product_soup)
            for product_soup in products
        ]

    @staticmethod
    def write_products_to_csv(csv_path: str, products: [Product]) -> None:
        with open(csv_path, "w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(PRODUCT_FIELDS)
            writer.writerows([astuple(product) for product in products])

    def get_all_products(self) -> None:
        with webdriver.Chrome() as new_driver:
            set_driver(new_driver)
            driver = get_driver()

            for url, csv_path in PAGES_TO_PARSE_WITH_SAVE_PATH:
                driver.get(url)

                check_cookies(driver)
                click_button_many_times(driver)

                page = driver.page_source
                soup = BeautifulSoup(page, "html.parser")

                products = self.get_single_page_products(soup)

                self.write_products_to_csv(
                    csv_path=csv_path, products=products
                )
