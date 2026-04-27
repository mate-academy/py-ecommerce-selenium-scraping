import csv
import logging
from dataclasses import dataclass, fields
from typing import List, Optional
from urllib.parse import urljoin

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

BASE_URL = "https://webscraper.io/test-sites/e-commerce/more/"


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


class FateScraper:
    def __init__(self, headless: bool = True):
        options = Options()
        if headless:
            options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        self.driver = webdriver.Chrome(options=options)
        self.wait = WebDriverWait(self.driver, 10)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.driver.quit()

    def accept_cookies(self):
        try:
            btn = WebDriverWait(self.driver, 2).until(
                EC.element_to_be_clickable((By.CLASS_NAME, "acceptCookies"))
            )
            btn.click()
        except:
            pass

    def click_more_until_done(self):
        while True:
            try:
                more_btn = self.driver.find_elements(By.CSS_SELECTOR, ".ecomerce-items-scroll-more")
                if not more_btn or not more_btn[0].is_displayed():
                    break

                current_count = len(self.driver.find_elements(By.CLASS_NAME, "thumbnail"))
                self.driver.execute_script("arguments[0].click();", more_btn[0])

                self.wait.until(
                    lambda d: len(d.find_elements(By.CLASS_NAME, "thumbnail")) > current_count
                )
            except Exception:
                break

    def extract_product_data(self, item) -> Optional[Product]:
        try:
            title_el = item.find_element(By.CLASS_NAME, "title")
            price_text = item.find_element(By.CLASS_NAME, "price").text.replace("$", "")

            # Надійний парсинг рейтингу (Спосіб А -> Спосіб Б)
            rating = 0
            try:
                rating_attr = item.find_element(By.CSS_SELECTOR, "p[data-rating]").get_attribute("data-rating")
                rating = int(rating_attr) if rating_attr else 0
            except:
                stars = item.find_elements(By.CSS_SELECTOR, ".ws-icon-star")
                rating = len(stars)

            try:
                reviews_text = item.find_element(By.CLASS_NAME, "review-count").text
                num_reviews = int(reviews_text.split()[0])
            except:
                num_reviews = 0

            return Product(
                title=title_el.get_attribute("title") or title_el.text,
                description=item.find_element(By.CLASS_NAME, "description").text,
                price=float(price_text),
                rating=rating,
                num_of_reviews=num_reviews
            )
        except Exception:
            return None

    def scrape_category(self, url: str) -> List[Product]:
        logging.info(f"Scraping: {url}")
        self.driver.get(url)
        self.accept_cookies()
        self.click_more_until_done()

        items = self.driver.find_elements(By.CLASS_NAME, "thumbnail")
        products = [self.extract_product_data(i) for i in items]
        return [p for p in products if p]


def write_products_to_csv(products: List[Product], filename: str):
    if not products:
        return
    header = [f.name for f in fields(Product)]
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=header)
        writer.writeheader()
        for p in products:
            writer.writerow(p.__dict__)


def get_all_products():
    """Основна функція згідно зі специфікацією."""
    PAGES = {
        "home": BASE_URL,
        "computers": urljoin(BASE_URL, "computers"),
        "laptops": urljoin(BASE_URL, "computers/laptops"),
        "tablets": urljoin(BASE_URL, "computers/tablets"),
        "phones": urljoin(BASE_URL, "phones"),
        "touch": urljoin(BASE_URL, "phones/touch"),
    }

    with FateScraper(headless=True) as scraper:
        for name, url in PAGES.items():
            data = scraper.scrape_category(url)
            write_products_to_csv(data, f"{name}.csv")


if __name__ == "__main__":
    get_all_products()