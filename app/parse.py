import csv
import time
from dataclasses import dataclass, astuple
from typing import Any

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.common.exceptions import TimeoutException

BASE_URL = "https://webscraper.io/test-sites/e-commerce/more/"
PAGES = {
    "home.csv": BASE_URL,
    "computers.csv": f"{BASE_URL}computers",
    "laptops.csv": f"{BASE_URL}computers/laptops",
    "tablets.csv": f"{BASE_URL}computers/tablets",
    "phones.csv": f"{BASE_URL}phones",
    "touch.csv": f"{BASE_URL}phones/touch",
}


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


def parse_single_product(card: Any) -> Product:
    title = card.select_one(".title").get("title")
    description = card.select_one(".description").text.strip()
    price = float(card.select_one(".price").text.replace("$", ""))

    rating_paragraph = card.select_one(".ratings p:not(.review-count)")
    rating = len(rating_paragraph.select("span")) if rating_paragraph else 0

    reviews_text = card.select_one(".review-count").text
    num_of_reviews = int(reviews_text.split()[0])

    return Product(title, description, price, rating, num_of_reviews)


def load_full_page_html(driver: webdriver.Chrome, url: str) -> str:
    driver.get(url)

    try:
        cookie_btn = WebDriverWait(driver, 2).until(
            expected_conditions.element_to_be_clickable((
                By.CSS_SELECTOR,
                "button[data-tid='banner-accept']"
            ))
        )
        cookie_btn.click()
    except TimeoutException:
        pass

    while True:
        try:
            more_button = WebDriverWait(driver, 2).until(
                expected_conditions.presence_of_element_located((
                    By.CSS_SELECTOR,
                    ".ecomerce-items-scroll-more"
                ))
            )
            if not more_button.is_displayed():
                break

            driver.execute_script("arguments[0].click();", more_button)
            time.sleep(0.5)
        except TimeoutException:
            break

    return driver.page_source


def get_all_products() -> None:
    options = webdriver.ChromeOptions()

    with webdriver.Chrome(options=options) as driver:
        for file_name, url in PAGES.items():
            html_source = load_full_page_html(driver, url)
            soup = BeautifulSoup(html_source, "html.parser")

            product_cards = soup.select(".card-body")
            products = [parse_single_product(card) for card in product_cards]

            with open(file_name, "w", newline="") as file:
                writer = csv.writer(file)
                writer.writerow([
                    "title",
                    "description",
                    "price",
                    "rating",
                    "num_of_reviews"
                ])
                writer.writerows([astuple(product) for product in products])


if __name__ == "__main__":
    get_all_products()
