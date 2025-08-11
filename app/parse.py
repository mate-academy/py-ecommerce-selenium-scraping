import csv
import re
import time
from dataclasses import dataclass
from typing import List
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

BASE_URL = "https://webscraper.io/"
PAGES = {
    "home": urljoin(BASE_URL, "test-sites/e-commerce/more/"),
    "computers": urljoin(BASE_URL, "test-sites/e-commerce/more/computers"),
    "laptops": urljoin(BASE_URL, "test-sites/e-commerce/more/computers/laptops"),
    "tablets": urljoin(BASE_URL, "test-sites/e-commerce/more/computers/tablets"),
    "phones": urljoin(BASE_URL, "test-sites/e-commerce/more/phones"),
    "touch": urljoin(BASE_URL, "test-sites/e-commerce/more/phones/touch"),
}

PAGINATED_PAGES = {"laptops", "tablets", "touch"}


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


def initialize_driver() -> webdriver.Chrome:
    options = Options()
    options.headless = True
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")

    driver = webdriver.Chrome(options=options)
    return driver


def accept_cookies(driver: webdriver.Chrome) -> None:
    try:
        btn = driver.find_element(By.ID, "accept-cookies")
        btn.click()
        time.sleep(0.3)
    except Exception:
        pass


def click_more_until_done(driver: webdriver.Chrome) -> None:
    wait = WebDriverWait(driver, 10)

    while True:
        try:
            more_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "a.ecomerce-items-scroll-more")))

            driver.execute_script("arguments[0].scrollIntoView();", more_btn)

            print("Clicking More button...")
            more_btn.click()
            time.sleep(1)

        except Exception:
            print("No more 'More' button found, or error occurred.")
            break


def parse_products(driver: webdriver.Chrome) -> List[Product]:
    soup = BeautifulSoup(driver.page_source, "html.parser")
    products = []

    for product in soup.select(".thumbnail"):
        title = product.select_one(".title").get_text(strip=True)
        description = product.select_one(".description").get_text(strip=True)
        price_str = product.select_one(".price").get_text(strip=True).replace("$", "")
        price = float(price_str)

        rating_tag = product.select_one(".ratings .rating")
        rating = int(rating_tag.get("data-rating")) if rating_tag else 0

        reviews_tag = product.select_one(".ratings .pull-right")
        if reviews_tag:
            match = re.search(r"\d+", reviews_tag.get_text(strip=True))
            num_of_reviews = int(match.group()) if match else 0
        else:
            num_of_reviews = 0

        products.append(Product(title, description, price, rating, num_of_reviews))

    return products


def save_to_csv(products: List[Product], filename: str) -> None:
    with open(filename, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Title", "Description", "Price", "Rating", "Number of Reviews"])
        for p in products:
            writer.writerow([p.title, p.description, p.price, p.rating, p.num_of_reviews])


def get_all_products() -> None:
    driver = initialize_driver()

    for page_name, page_url in PAGES.items():
        driver.get(page_url)
        accept_cookies(driver)

        if page_name in PAGINATED_PAGES:
            click_more_until_done(driver)

        products = parse_products(driver)
        print(f"Scraped {len(products)} products from {page_name} page")

        filename = f"{page_name}.csv"
        save_to_csv(products, filename)
        print(f"Saved {len(products)} products to {filename}")

    driver.quit()


if __name__ == "__main__":
    get_all_products()
