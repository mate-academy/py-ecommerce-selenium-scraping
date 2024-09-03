import csv
import time
from dataclasses import dataclass
from selenium import webdriver
from selenium.common import NoSuchElementException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from tqdm import tqdm

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")

@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


def parse_product_data(product_element):
    """Parses the product data from a single product element."""
    title = product_element.select_one(".title").text.strip()
    description = product_element.select_one(".description").text.strip()
    price = float(product_element.select_one(".price").
                  text.replace("$", "").strip())
    rating = int(product_element.select_one(".ratings > p[data-rating]").
                 attrs.get("data-rating", "0"))
    num_of_reviews = int(product_element.select_one(
        ".ratings > p.pull-right").text.split()[0])

    return Product(title=title,
                   description=description,
                   price=price,
                   rating=rating,
                   num_of_reviews=num_of_reviews)


def save_to_csv(filename, products):
    """Saves a list of Product objects to a CSV file."""
    with open(filename, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["Title", "Description", "Price", "Rating", "Number of Reviews"])
        for product in products:
            writer.writerow(
                [product.title,
                 product.description,
                 product.price,
                 product.rating,
                 product.num_of_reviews]
            )


def get_all_products():
    options = Options()
    options.headless = True
    service = Service("./chromedriver")
    driver = webdriver.Chrome(service=service, options=options)

    driver.get(HOME_URL)
    try:
        accept_cookies = driver.find_element(
            By.ID, "onetrust-accept-btn-handler"
        )
        accept_cookies.click()
        time.sleep(1)
    except NoSuchElementException:
        print("Accept cookies button not found. Continuing...")

    pages = [
        {"url": HOME_URL, "filename": "home.csv"},
        {"url": urljoin(HOME_URL, "computers"), "filename": "computers.csv"},
        {"url": urljoin(HOME_URL, "laptops"), "filename": "laptops.csv"},
        {"url": urljoin(HOME_URL, "tablets"), "filename": "tablets.csv"},
        {"url": urljoin(HOME_URL, "phones"), "filename": "phones.csv"},
        {"url": urljoin(HOME_URL, "touch"), "filename": "touch.csv"},
    ]

    for page in tqdm(pages, desc="Scraping pages"):
        driver.get(page["url"])
        products = []

        while True:
            soup = BeautifulSoup(driver.page_source, "html.parser")
            product_elements = soup.select(".thumbnail")

            for product_element in product_elements:
                product = parse_product_data(product_element)
                products.append(product)

            try:
                more_button = driver.find_element(
                    By.CLASS_NAME, "btn.btn-default")
                more_button.click()
                time.sleep(1)
            except Exception:
                break

        save_to_csv(page["filename"], products)

    driver.quit()
