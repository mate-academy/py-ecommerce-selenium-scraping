import csv
import time
from dataclasses import dataclass
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


driver = webdriver.Chrome()
wait = WebDriverWait(driver, 10)

def accept_cookies():
    try:
        cookies_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[text()='Accept']")))
        cookies_button.click()
        print("Accepted cookies.")
    except (NoSuchElementException, TimeoutException):
        print("No cookies button found.")

def scrape_page(url, paginate=False):
    driver.get(url)
    accept_cookies()

    products = []

    if paginate:
        while True:
            try:
                load_more_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".load-more-button")))
                ActionChains(driver).move_to_element(load_more_button).click(load_more_button).perform()
                time.sleep(1)
            except (NoSuchElementException, TimeoutException):
                print("No more pages to load.")
                break

    soup = BeautifulSoup(driver.page_source, "html.parser")
    items = soup.select(".col-md-4")

    for item in items:
        title = item.select_one("a.title").text.strip() if item.select_one("a.title") else "No title"

        price_text = item.select_one("h4.price").text.strip() if item.select_one("h4.price") else "0"
        price = float(price_text.replace("$", "")) if price_text else 0.0

        description = item.select_one("p.card-text").text.strip() if item.select_one("p.card-text") else "No description"

        rating = len(item.select(".fa.fa-star"))

        num_of_reviews_text = item.select_one(".ratings .pull-right").text.strip() if item.select_one(
            ".ratings .pull-right") else "0 reviews"
        num_of_reviews = int(num_of_reviews_text.split()[0]) if num_of_reviews_text else 0

        products.append(Product(title, description, price, rating, num_of_reviews))

    return products

def save_to_csv(products, filename):
    with open(filename, mode="w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=["title", "description", "price", "rating", "num_of_reviews"])
        writer.writeheader()
        for product in products:
            writer.writerow({
                "title": product.title,
                "description": product.description,
                "price": product.price,
                "rating": product.rating,
                "num_of_reviews": product.num_of_reviews
            })
        print(f"Saved {len(products)} products to {filename}")

def get_all_products():
    pages = {
        "home.csv": "https://webscraper.io/test-sites/e-commerce/more/",
        "computers.csv": "https://webscraper.io/test-sites/e-commerce/more/computers",
        "laptops.csv": "https://webscraper.io/test-sites/e-commerce/more/computers/laptops",
        "tablets.csv": "https://webscraper.io/test-sites/e-commerce/more/computers/tablets",
        "phones.csv": "https://webscraper.io/test-sites/e-commerce/more/phones",
        "touch.csv": "https://webscraper.io/test-sites/e-commerce/more/phones/touch"
    }

    for filename, url in pages.items():
        paginate = filename in ["laptops.csv", "tablets.csv", "touch.csv"]
        products = scrape_page(url, paginate=paginate)
        save_to_csv(products, filename)

if __name__ == "__main__":
    get_all_products()
    driver.quit()
