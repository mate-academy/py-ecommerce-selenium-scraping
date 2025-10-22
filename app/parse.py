from urllib.parse import urljoin
from selenium import webdriver
import csv

from app.parser import Parser
from app.schemas import Product


BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")


def _write_csv(filename: str, products: list[Product]) -> None:
    with open(filename, "w", encoding="utf-8", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["title", "description", "price", "rating", "num_of_reviews"])
        for p in products:
            writer.writerow([p.title, p.description, p.price, p.rating, p.num_of_reviews])


def get_all_products() -> None:
    pages = {
        "home": urljoin(HOME_URL, ""),
        "computers": urljoin(HOME_URL, "computers"),
        "laptops": urljoin(HOME_URL, "computers/laptops"),
        "tablets": urljoin(HOME_URL, "computers/tablets"),
        "phones": urljoin(HOME_URL, "phones"),
        "touch": urljoin(HOME_URL, "phones/touch"),
    }

    with webdriver.Chrome() as driver:
        parser = Parser(driver)
        for name, url in pages.items():
            products = parser.parse_page(url)
            _write_csv(f"{name}.csv", products)


if __name__ == "__main__":
    get_all_products()
