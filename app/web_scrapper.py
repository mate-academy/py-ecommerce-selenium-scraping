import csv
from dataclasses import astuple
from typing import List

from selenium import webdriver
from selenium.common import (
    NoSuchElementException,
    ElementClickInterceptedException,
    ElementNotInteractableException
)
from selenium.webdriver import ActionChains
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from tqdm import tqdm

from app.product_class import PRODUCT_FIELDS, Product


class WebScraper:
    BASE_URL = "https://webscraper.io/test-sites/e-commerce/more/"

    def __init__(self) -> None:
        opts = Options()
        opts.add_argument("--headless")
        self.driver = webdriver.Chrome(options=opts)
        self.driver.get(WebScraper.BASE_URL)
        self._accept_cookies()
        self._parse_all_pages()
        self.driver.close()

    def _accept_cookies(self) -> None:
        try:
            accept_cookies_button = self.driver.find_element(
                By.CLASS_NAME, "acceptCookies"
            )
            accept_cookies_button.click()
        except NoSuchElementException:
            return

    def _get_correct_links_from_sidebar(self) -> List[WebElement]:
        return self.driver.find_elements(
            By.CSS_SELECTOR, ".nav-item > .nav-link"
        )[6:]

    def _parse_and_write_products_from_single_page_to_file(
            self,
            link: WebElement
    ) -> None:
        csv_file_name = link.text.lower() + ".csv"

        ActionChains(self.driver).move_to_element(link).click().perform()

        products = self._get_single_page_products()
        self._write_data_to_csv(csv_file_name, products, PRODUCT_FIELDS)

    def _parse_all_pages(self) -> None:
        links = self._get_correct_links_from_sidebar()
        link_index = 0

        while link_index <= len(links):
            self._parse_and_write_products_from_single_page_to_file(
                links[link_index]
            )
            links = self._get_correct_links_from_sidebar()
            link_index += 1

        self._parse_and_write_products_from_single_page_to_file(links[-1])

    @staticmethod
    def _parse_single_product(product: WebElement) -> Product:
        return Product(
            title=product.find_element(
                By.CSS_SELECTOR, ".title"
            ).get_property("title"),
            description=product.find_element(
                By.CSS_SELECTOR, ".description"
            ).text,
            price=float(product.find_element(
                By.CLASS_NAME, "price"
            ).text.replace("$", "")),
            rating=len(product.find_elements(By.CLASS_NAME, "ws-icon-star")),
            num_of_reviews=int(
                product.find_element(By.CLASS_NAME, "review-count")
                .text.split()[0]
            ),
        )

    def _get_single_page_products(self) -> List[Product]:
        self._click_more_button()
        products = self.driver.find_elements(By.CLASS_NAME, "thumbnail")

        return [self._parse_single_product(product) for product in tqdm(products)]

    def _click_more_button(self) -> None:
        while True:
            try:
                more_button = self.driver.find_element(
                    By.CLASS_NAME, "ecomerce-items-scroll-more"
                )
                more_button.click()
            except (
                    NoSuchElementException,
                    ElementClickInterceptedException,
                    ElementNotInteractableException
            ):
                return

    @staticmethod
    def _write_data_to_csv(
            output_csv_path: str,
            scrapped_data: List[Product],
            field_names: List[str]
    ) -> None:
        with open(output_csv_path, "w", encoding="utf-8", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(field_names)
            writer.writerows([astuple(data) for data in scrapped_data])
            print(f"File '{output_csv_path}' was successfully created")
