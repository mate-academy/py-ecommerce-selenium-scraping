from dataclasses import dataclass
from lib2to3.pgen2 import driver
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import csv
from typing import List


BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")

@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int

PAGES = {
    "home": urljoin(BASE_URL, "test-sites/e-commerce/more/"),
    "computers": urljoin(BASE_URL, "test-sites/e-commerce/more/computers"),
    "laptops": urljoin(BASE_URL, "test-sites/e-commerce/more/laptops"),
    "tablets": urljoin(BASE_URL, "test-sites/e-commerce/more/tablets"),
    "phones": urljoin(BASE_URL, "test-sites/e-commerce/more/phones"),
    "touch": urljoin(BASE_URL, "test-sites/e-commerce/more/touch"),
}

def initialize_driver():
    options = Options()
    options.headless = True
    driver = webdriver.Chrome(options=options)
    return driver


def parse_products(driver):
    soup = BeautifulSoup(driver.page_source, "html.parser")
    products = []

    for product in soup.select(".thumbnail"):  # Select each product thumbnail
        title = product.select_one(".title").get_text(strip=True)
        description = product.select_one(".description").get_text(strip=True)
        price = float(product.select_one(".price").get_text(strip=True).replace("$", ""))

        # Check if rating element is present
        rating_tag = product.select_one(".ratings .rating")
        rating = int(rating_tag.get("data-rating")) if rating_tag else 0

        # Check if number of reviews element is present
        reviews_tag = product.select_one(".ratings .pull-right")
        num_of_reviews = int(reviews_tag.get_text(strip=True).split()[0]) if reviews_tag else 0

        products.append(Product(title, description, price, rating, num_of_reviews))

    return products


def save_to_csv(products: List[Product], filename: str) -> None:
    with open(filename, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        # Write header
        writer.writerow(["Title", "Description", "Price", "Rating", "Number of Reviews"])
        # Write product data
        for product in products:
            writer.writerow([product.title, product.description, product.price, product.rating, product.num_of_reviews])

def get_all_products() -> None:
    driver = initialize_driver()

    for page_name, page_url in PAGES.items():
        driver.get(page_url)
        products = parse_products(driver)
        print(f"Scraped {len(products)} products from {page_name} page")

        filename = f"{page_name}.csv"
        save_to_csv(products, filename)
        print(f"Saved {len(products)} products to {filename}")

    driver.quit()

if __name__ == "__main__":
    get_all_products()


