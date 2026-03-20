import csv
import logging
import time
from dataclasses import dataclass, fields, astuple
from urllib.parse import urljoin

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from bs4 import BeautifulSoup

# Налаштування логування
logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s]: %(message)s"
)

BASE_URL = "https://webscraper.io/test-sites/e-commerce/more/"


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


PRODUCT_FIELDS = [field.name for field in fields(Product)]


def get_driver():
    options = Options()
    options.add_argument("--headless")  # Запуск без вікна
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    return webdriver.Chrome(options=options)


def parse_page(driver, url, filename):
    logging.info(f"Parsing {url} -> {filename}")
    driver.get(url)

    # Приймаємо кукі
    try:
        WebDriverWait(driver, 2).until(
            EC.element_to_be_clickable((By.CLASS_NAME, "acceptCookies"))
        ).click()
    except:
        pass

    # Тиснемо "More", поки є
    while True:
        try:
            more_button = WebDriverWait(driver, 1).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, ".btn-primary.loadMore"))
            )
            driver.execute_script("arguments[0].click();", more_button)
        except:
            break

    # Даємо пів секунди на фінальний рендеринг після останнього кліку
    time.sleep(0.5)

    soup = BeautifulSoup(driver.page_source, "html.parser")
    products = []

    for card in soup.select(".thumbnail"):
        # УНІВЕРСАЛЬНИЙ РЕЙТИНГ
        rating_el = card.select_one("p[data-rating]")
        if rating_el:
            rating = int(rating_el["data-rating"])
        else:
            rating = len(card.select(".glyphicon-star"))

        # ВІДГУКИ
        reviews_el = card.select_one(".review-count")
        num_of_reviews = int(reviews_el.text.split()[0]) if reviews_el else 0

        # ЦІНА
        price_el = card.select_one(".price")
        price = float(price_el.text.replace("$", "")) if price_el else 0.0

        products.append(Product(
            title=card.select_one(".title")["title"],
            description=card.select_one(".description").text.strip(),
            price=price,
            rating=rating,
            num_of_reviews=num_of_reviews
        ))

    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(PRODUCT_FIELDS)
        for p in products:
            writer.writerow(astuple(p))


def get_all_products():
    pages = [
        {"url": "", "file": "home.csv"},
        {"url": "computers", "file": "computers.csv"},
        {"url": "computers/laptops", "file": "laptops.csv"},
        {"url": "computers/tablets", "file": "tablets.csv"},
        {"url": "phones", "file": "phones.csv"},
        {"url": "phones/touch", "file": "touch.csv"},
    ]

    driver = get_driver()
    try:
        for page in pages:
            full_url = urljoin(BASE_URL, page["url"])
            parse_page(driver, full_url, page["file"])
    finally:
        driver.quit()


if __name__ == "__main__":
    get_all_products()
