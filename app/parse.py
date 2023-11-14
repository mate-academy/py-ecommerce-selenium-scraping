import csv
import logging
from urllib.parse import urljoin
from dataclasses import dataclass

from selenium import webdriver
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    ElementClickInterceptedException,
    ElementNotInteractableException
)


BASE_URL = "https://webscraper.io/"

urls = {
    "home": urljoin(BASE_URL, "test-sites/e-commerce/more/"),
    "computers": urljoin(BASE_URL, "test-sites/e-commerce/more/computers"),
    "laptops": urljoin(
        BASE_URL, "test-sites/e-commerce/more/computers/laptops"
    ),
    "tablets": urljoin(
        BASE_URL, "test-sites/e-commerce/more/computers/tablets"
    ),
    "phones": urljoin(BASE_URL, "test-sites/e-commerce/more/phones"),
    "touch": urljoin(BASE_URL, "test-sites/e-commerce/more/phones/touch"),
}

logging.basicConfig(level=logging.INFO)


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


def parse_single_product(product_soup: BeautifulSoup) -> Product:
    title_elem = product_soup.select_one(".title")
    description_elem = product_soup.select_one(".description")
    price_elem = product_soup.select_one(".price")
    rating_elem = product_soup.select_one("p[data-rating]")
    review_elem = product_soup.select_one(".review-count")

    title = title_elem["title"] if title_elem else ""
    description = description_elem.text if description_elem else ""
    price = float(price_elem.text.replace("$", "")) if price_elem else 0.0
    rating = int(rating_elem["data-rating"]) if rating_elem else 0
    num_of_reviews = (
        int(review_elem.text.split()[0].replace("$", "")) if review_elem else 0
    )

    return Product(
        title=title,
        description=description,
        price=price,
        rating=rating,
        num_of_reviews=num_of_reviews,
    )


def get_all_products() -> [Product]:
    driver = webdriver.Chrome()

    for url_key, url_value in urls.items():
        logging.info(f"Start process {url_key} page")
        driver.get(url_value)

        cookies = driver.find_elements(By.CLASS_NAME, "acceptCookies")

        if cookies and cookies[0].is_displayed() and cookies[0].is_enabled():
            cookies[0].click()

        try:
            button_more = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.CLASS_NAME, "ecomerce-items-scroll-more"))
            )
            while button_more.is_enabled() and button_more.is_displayed():
                button_more.click()
                logging.info("Clicked")
        except (
            TimeoutException,
            ElementClickInterceptedException,
            ElementNotInteractableException
        ):
            logging.info("'More' button is unavailable or not found")

        soup = BeautifulSoup(driver.page_source, "html.parser")

        url_products = soup.select(".card-body")

        products = [
            parse_single_product(product_soup) for product_soup in url_products
        ]

        save_products(f"{url_key}.csv", products)

    driver.quit()


def save_products(filename: str, products: [Product]) -> None:
    fieldnames = ["title", "price", "description", "rating", "num_of_reviews"]

    with open(filename, mode="w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()

        for product in products:
            product_data = {
                "title": product.title,
                "description": product.description,
                "price": product.price,
                "rating": product.rating,
                "num_of_reviews": product.num_of_reviews,
            }
            writer.writerow(product_data)


if __name__ == "__main__":
    get_all_products()
