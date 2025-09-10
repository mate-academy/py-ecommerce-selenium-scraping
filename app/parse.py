import csv
import time
from typing import List
from dataclasses import dataclass, fields, astuple

from tqdm import tqdm
from urllib.parse import urljoin
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support import expected_conditions as ec


BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


PRODUCT_FIELDS = [field.name for field in fields(Product)]


def get_driver(headless: bool = True) -> webdriver.Chrome:
    options = Options()
    if headless:
        options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(options=options)
    return driver


def accept_cookies(driver: webdriver.Chrome) -> None:
    try:
        btn = WebDriverWait(driver, 5).until(
            ec.element_to_be_clickable((By.CLASS_NAME, "acceptCookies"))
        )
        btn.click()
    except TimeoutException:
        pass


def scroll_and_load(driver: webdriver.Chrome) -> None:
    while True:
        try:
            more_button = WebDriverWait(driver, 3).until(
                ec.element_to_be_clickable((By.CLASS_NAME, "btn-primary"))
            )
            driver.execute_script("arguments[0].click();", more_button)
            time.sleep(1)
        except TimeoutException:
            break


def parse_products_from_page(driver: webdriver.Chrome) -> List[Product]:
    items = driver.find_elements(By.CLASS_NAME, "thumbnail")
    products = []

    for item in items:
        title = item.find_element(
            By.CLASS_NAME, "title"
        ).get_attribute("title").strip()
        description = item.find_element(
            By.CLASS_NAME, "description"
        ).text.strip()
        price_text = item.find_element(
            By.CLASS_NAME, "price"
        ).text.strip().replace("$", "")
        rating = len(item.find_elements(By.CLASS_NAME, "ws-icon-star"))
        reviews_text = item.find_element(By.CLASS_NAME, "ratings").text
        num_of_reviews = int(reviews_text.split(" ")[0])

        products.append(Product(
            title=title,
            description=description,
            price=float(price_text),
            rating=rating,
            num_of_reviews=num_of_reviews
        ))

    return products


def save_to_csv(products: List[Product], filename: str) -> None:
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(PRODUCT_FIELDS)
        for product in products:
            writer.writerow(astuple(product))


def process_page(url: str, output_csv: str, use_scroll: bool = False) -> None:
    driver = get_driver()
    driver.get(url)
    accept_cookies(driver)

    if use_scroll:
        scroll_and_load(driver)

    products = parse_products_from_page(driver)
    save_to_csv(products, output_csv)
    driver.quit()


def get_all_products() -> None:
    pages = [
        ("home", HOME_URL, False),
        ("computers", urljoin(HOME_URL, "computers"), False),
        ("laptops", urljoin(HOME_URL, "computers/laptops"), True),
        ("tablets", urljoin(HOME_URL, "computers/tablets"), True),
        ("phones", urljoin(HOME_URL, "phones"), False),
        ("touch", urljoin(HOME_URL, "phones/touch"), True),
    ]

    for name, url, scroll in tqdm(pages, desc="Pages"):
        tqdm.write(f"Scraping page: {name} ({url})...")
        process_page(url, f"{name}.csv", use_scroll=scroll)
        tqdm.write(f" Done: {name}")


if __name__ == "__main__":
    get_all_products()
