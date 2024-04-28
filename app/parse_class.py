import csv
from dataclasses import dataclass
from typing import List
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


class ParseClass:

    BASE_URL = "https://webscraper.io/"
    HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")

    def __init__(self, gadget_type: str = None) -> None:
        self.gadget_type = gadget_type
        self.file_name = "home.csv" if not gadget_type else None
        self.url = urljoin(ParseClass.HOME_URL, gadget_type)
        self.options = webdriver.ChromeOptions()
        self.options.add_experimental_option("detach", True)
        self.driver = webdriver.Chrome(options=self.options)
        self.products: List[Product] = []

    @staticmethod
    def parse_product_rating(soup: BeautifulSoup) -> int:
        product_rating = str(soup.select_one(".review-count"))
        return product_rating.count("ws-icon ws-icon-star")

    @staticmethod
    def parse_product_reviews(soup: BeautifulSoup) -> int:
        reviews = soup.select_one(".review-count").text.split()[0]
        return int(reviews)

    @staticmethod
    def parse_single_product(soup: BeautifulSoup) -> Product:
        single_product = Product(
            title=soup.find("h4", {"class": "title card-title"}).text,
            description=soup.find(
                "p", {"class": "description card-text"
                      }).text,
            price=float(soup.select_one(".price").text.replace("$", "")),
            rating=ParseClass.parse_product_rating(soup),
            num_of_reviews=ParseClass.parse_product_reviews(soup),
        )
        return single_product

    def open_all_products(self) -> None:
        self.driver.get(self.url)
        while True:
            more = self.driver.find_elements(By.LINK_TEXT, "More")
            if more:
                actions = ActionChains(self.driver)
                actions.move_to_element(more[0]).click().perform()
            else:
                break

    # ""
    def parse_all_products(self) -> List[Product]:
        links = self.driver.find_elements(By.CLASS_NAME, "title")
        for link in links:
            product_url = link.get_attribute("href")
            product_page = requests.get(product_url)
            soup = BeautifulSoup(product_page.text, "html.parser")
            product = self.parse_single_product(soup)
            self.products.append(product)
        return self.products

    def get_file_name(self) -> None:
        if not self.file_name:
            if "/" not in self.gadget_type:
                self.file_name = f"{self.gadget_type}.csv"
            else:
                name = self.gadget_type.split("/")[-1]
                self.file_name = f"{name}.csv"

    def save_results(self) -> None:
        with open(self.file_name, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                "title", "description", "price", "rating", "num_of_reviews"
            ])
            for product in self.products:
                writer.writerow([
                    product.title,
                    product.description,
                    product.price,
                    product.rating,
                    product.num_of_reviews]
                )

    def parse_processing(self) -> None:
        self.open_all_products()
        self.parse_all_products()
        self.get_file_name()
        self.save_results()
        self.driver.close()
