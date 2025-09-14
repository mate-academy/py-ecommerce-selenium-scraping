from dataclasses import dataclass
from typing import List
from urllib.parse import urljoin
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC  # noqa: N812
from selenium.common.exceptions import TimeoutException
import csv
import time
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


def get_driver(headless=True):
    options = Options()
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(options=options)
    return driver


def accept_cookies(driver):
    try:
        btn = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.CLASS_NAME, "acceptCookies"))
        )
        btn.click()
    except TimeoutException:
        pass


def wait_for_thumbnails(driver, timeout: int = 8, min_count: int = 1) -> None:
    WebDriverWait(driver, timeout).until(
        lambda d: len(d.find_elements(By.CLASS_NAME, "thumbnail")) >= min_count
    )


def scroll_and_load(driver):
    while True:
        try:
            more_button = WebDriverWait(driver, 3).until(
                EC.element_to_be_clickable((By.CLASS_NAME, "btn-primary"))
            )
            before = len(driver.find_elements(By.CLASS_NAME, "thumbnail"))

            driver.execute_script("arguments[0].click();", more_button)
            WebDriverWait(driver, 5).until(
                lambda d: len(d.find_elements(By.CLASS_NAME, "thumbnail")) > before
            )

        except TimeoutException:
            break


def parse_products_from_page(driver) -> List[Product]:
    items = driver.find_elements(By.CLASS_NAME, "thumbnail")
    products = []

    for item in items:
        title_el = item.find_element(By.CLASS_NAME, "title")
        title = title_el.get_attribute("title").strip()

        description = item.find_element(By.CLASS_NAME, "description").text.strip()

        price_text = (
            item.find_element(By.CLASS_NAME, "price").text.strip().replace("$", "")
        )
        price = float(price_text)

        rating = len(item.find_elements(By.CLASS_NAME, "ws-icon-star"))

        reviews_text = item.find_element(By.CLASS_NAME, "review-count").text.strip()
        num_of_reviews = int(reviews_text.split(" ")[0])

        products.append(
            Product(
                title=title,
                description=description,
                price=price,
                rating=rating,
                num_of_reviews=num_of_reviews,
            )
        )

    return products


def save_to_csv(products: List[Product], filename: str):
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["title", "description", "price", "rating", "num_of_reviews"])
        for p in products:
            writer.writerow(
                [p.title, p.description, p.price, p.rating, p.num_of_reviews]
            )


def process_page(url: str, output_csv: str, use_scroll: bool = False):
    driver = get_driver()
    driver.get(url)
    accept_cookies(driver)

    wait_for_thumbnails(driver, timeout=8, min_count=1)

    if use_scroll:
        scroll_and_load(driver)
        wait_for_thumbnails(driver, timeout=5, min_count=1)

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

    for name, url, scroll in tqdm(pages, desc="Scraping pages"):
        process_page(url, f"{name}.csv", use_scroll=scroll)


if __name__ == "__main__":
    get_all_products()
