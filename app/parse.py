import csv
import time
from dataclasses import dataclass, asdict
from typing import List
from urllib.parse import urljoin

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


def init_driver() -> webdriver.Chrome:
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(options=options)
    return driver


def accept_cookies(driver: webdriver.Chrome) -> None:
    try:
        cookies_button = WebDriverWait(driver, 10).until(
            ec.element_to_be_clickable(
                (By.CLASS_NAME, "accept-cookies-button")
            )
        )
        cookies_button.click()
    except Exception:
        pass


def parse_products(driver: webdriver.Chrome) -> List[Product]:
    products = []
    product_elements = driver.find_elements(By.CLASS_NAME, "thumbnail")
    for product_element in product_elements:
        title = product_element.find_element(
            By.CLASS_NAME, "title"
        ).get_attribute("title").strip()

        description = product_element.find_element(
            By.CLASS_NAME, "description"
        ).text.strip()

        price = float(product_element.find_element(
            By.CLASS_NAME, "price"
        ).text.replace("$", "").strip())

        rating = len(product_element.find_element(
            By.CLASS_NAME, "ratings"
        ).find_elements(By.CLASS_NAME, "ws-icon-star"))

        num_of_reviews = int(product_element.find_element(
            By.CLASS_NAME, "review-count"
        ).text.split()[0])

        products.append(
            Product(
                title=title,
                description=description,
                price=price,
                rating=rating,
                num_of_reviews=num_of_reviews
            )
        )

    return products


def load_more_pages(driver: webdriver.Chrome) -> None:
    while True:
        try:
            more_button = WebDriverWait(driver, 10).until(
                ec.element_to_be_clickable((By.CLASS_NAME, "btn-primary"))
            )
            more_button.click()
            time.sleep(2)
        except Exception:
            break


def save_to_csv(file_name: str, products: List[Product]) -> None:
    if not products:
        print(f"No products found for {file_name}. Skipping file creation.")
        return

    with open(file_name, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=asdict(products[0]).keys())
        writer.writeheader()
        for product in products:
            writer.writerow(asdict(product))


def scrape_page(
        driver: webdriver.Chrome,
        url: str,
        file_name: str,
        has_pagination: bool = False
) -> None:
    driver.get(url)
    accept_cookies(driver)

    if has_pagination:
        load_more_pages(driver)

    products = parse_products(driver)

    save_to_csv(file_name, products)


def get_all_products() -> None:
    driver = init_driver()
    try:
        pages = [
            ("home", HOME_URL, False),
            ("computers", urljoin(HOME_URL, "computers"), False),
            ("laptops", urljoin(HOME_URL, "computers/laptops"), True),
            ("tablets", urljoin(HOME_URL, "computers/tablets"), True),
            ("phones", urljoin(HOME_URL, "phones"), False),
            ("touch", urljoin(HOME_URL, "phones/touch"), True),
        ]

        for name, url, has_pagination in pages:
            file_name = f"{name}.csv"
            scrape_page(driver, url, file_name, has_pagination)
    finally:
        driver.quit()


if __name__ == "__main__":
    get_all_products()
