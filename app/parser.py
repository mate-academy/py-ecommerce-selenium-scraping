from typing import List
from urllib.parse import urljoin
import csv

from selenium import webdriver
from selenium.common import NoSuchElementException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

from bs4 import BeautifulSoup, Tag
from selenium.webdriver.remote.webdriver import WebDriver
from tqdm import tqdm

from app.enitity import Product


class Parser:
    HOME_URL = "https://webscraper.io/test-sites/e-commerce/more/"

    AVAILABLE_URLS = {
        "home": HOME_URL,
        "computers": urljoin(HOME_URL, "computers"),
        "laptops": urljoin(HOME_URL, "computers/laptops"),
        "tablets": urljoin(HOME_URL, "computers/tablets"),
        "phones": urljoin(HOME_URL, "phones"),
        "touch": urljoin(HOME_URL, "phones/touch")
    }

    def __init__(self) -> None:
        self.driver = self.__initialize_driver()

    def parse(self) -> None:
        for category, url in Parser.AVAILABLE_URLS.items():
            self.__generate_all_items(
                category=category,
                url=url
            )

    def __generate_all_items(self, category: str, url: str) -> None:
        soup = self.__process_more_button(url=url)
        products_content = soup.select(".thumbnail")

        products = [
            self.__process_single_product(product_content)
            for product_content in tqdm(
                products_content,
                desc=f"Parsing{category}"
            )
        ]

        self.__write_product_to_file(
            category=category,
            products=products
        )

    def __process_single_product(self, product_content: Tag) -> Product:
        title = product_content.select_one(".title").get("title")
        description = product_content.select_one(
            ".description"
        ).text.replace("\xa0", " ")
        rating = len(product_content.select(".ratings span"))
        num_of_reviews = int(product_content.select_one(
            ".ratings > p"
        ).text.strip().split()[0])
        price = float(
            product_content.select_one(
                ".price"
            ).text.replace("$", "")
        )

        return Product(
            title=title,
            description=description,
            rating=rating,
            num_of_reviews=num_of_reviews,
            price=price
        )

    def __accept_cookies(self) -> None:
        try:
            cookies_button = self.driver.find_element(
                By.CSS_SELECTOR,
                "#cookieBanner > div.acceptContainer > a"
            )
            cookies_button.click()
        except NoSuchElementException:
            pass

    def __process_more_button(self, url: str) -> BeautifulSoup:
        self.driver.get(url)
        self.__accept_cookies()

        try:
            button_more = self.driver.find_element(
                By.CLASS_NAME,
                "ecomerce-items-scroll-more"
            )
            while button_more and button_more.is_displayed():
                button_more.click()
        except NoSuchElementException:
            pass
        finally:
            return BeautifulSoup(
                self.driver.page_source,
                "html.parser"
            )

    def __write_product_to_file(
            self,
            category: str,
            products: List[Product]
    ) -> None:
        with open(
                f"{category}.csv",
                "w+",
                newline="",
                encoding="utf-8"
        ) as home_file:
            fieldnames = [
                "title",
                "description",
                "price",
                "rating",
                "num_of_reviews"
            ]
            writer = csv.DictWriter(home_file, fieldnames=fieldnames)
            writer.writeheader()

            for product in products:
                writer.writerow({
                    "title": product.title,
                    "description": product.description,
                    "price": product.price,
                    "rating": product.rating,
                    "num_of_reviews": product.num_of_reviews
                })

    @staticmethod
    def __initialize_driver() -> WebDriver:
        chrome_options = Options()
        chrome_options.add_argument("--headless")

        return webdriver.Chrome(options=chrome_options)
