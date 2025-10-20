import csv
import time
from dataclasses import dataclass
from urllib.parse import urljoin

from selenium import webdriver
from selenium.common.exceptions import (
    NoSuchElementException,
    TimeoutException,
    StaleElementReferenceException
)
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")

PAGES = {
    "home": HOME_URL,
    "computers": urljoin(BASE_URL, "test-sites/e-commerce/more/computers"),
    "laptops": urljoin(BASE_URL, "test-sites/e-commerce/more/computers/laptops"),
    "tablets": urljoin(BASE_URL, "test-sites/e-commerce/more/computers/tablets"),
    "phones": urljoin(BASE_URL, "test-sites/e-commerce/more/phones"),
    "touch": urljoin(BASE_URL, "test-sites/e-commerce/more/phones/touch"),
}


_driver: WebDriver | None = None


def get_driver() -> WebDriver:
    if _driver is None:
        raise RuntimeError("Driver not set; call set_driver() first")
    return _driver


def set_driver(new_driver: WebDriver) -> None:
    global _driver
    _driver = new_driver


def accept_cookies() -> None:
    driver = get_driver()
    try:
        accept_btn = WebDriverWait(driver, 3).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, ".acceptCookies"))
        )
        accept_btn.click()
        time.sleep(0.5)
    except (TimeoutException, NoSuchElementException):
        pass


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int

def parse_product(product_element) -> Product:
    title_el = product_element.find_element(By.CLASS_NAME, "title")
    title = title_el.get_attribute("title")

    description = product_element.find_element(By.CLASS_NAME, "description").text.strip()

    price_text = product_element.find_element(By.CLASS_NAME, "price").text.strip()
    price = float(price_text.replace("$", ""))

    ratings_el = product_element.find_element(By.CLASS_NAME, "ratings")
    stars = ratings_el.find_elements(By.CLASS_NAME, "ws-icon-star")
    rating = len(stars)

    review_count_text = ratings_el.find_element(By.CLASS_NAME, "review-count").text.strip()
    num_of_reviews = int(review_count_text.split()[0])

    return Product(title=title, description=description, price=price, rating=rating, num_of_reviews=num_of_reviews)


def load_all_products_on_page() -> None:
    driver = get_driver()
    while True:
        try:
            more_btn = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.CLASS_NAME, "ecomerce-items-scroll-more"))
            )
        except (TimeoutException, NoSuchElementException):
            break

        prev_count = len(driver.find_elements(By.CLASS_NAME, "thumbnail"))

        try:
            more_btn.click()
        except StaleElementReferenceException:
            continue

        try:
            WebDriverWait(driver, 10).until(
                lambda d: len(d.find_elements(By.CLASS_NAME, "thumbnail")) > prev_count
                          or _more_button_gone(more_btn)
            )
        except TimeoutException:
            continue

def _more_button_gone(more_btn) -> bool:
    try:
        return not more_btn.is_displayed()
    except StaleElementReferenceException:
        return True


def scrape_page(url: str, page_name: str) -> list[Product]:
    driver = get_driver()
    driver.get(url)

    accept_cookies()
    load_all_products_on_page()

    product_elements = driver.find_elements(By.CLASS_NAME, "thumbnail")
    products: list[Product] = []
    for el in product_elements:
        products.append(parse_product(el))

    return products


def save_to_csv(products: list[Product], filename: str) -> None:
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["title", "description", "price", "rating", "num_of_reviews"])
        for p in products:
            writer.writerow([p.title, p.description, p.price, p.rating, p.num_of_reviews])


def get_all_products(driver: WebDriver | None = None, options: webdriver.ChromeOptions | None = None) -> None:
    if driver is not None:
        set_driver(driver)
        for page_name, page_url in PAGES.items():
            products = scrape_page(page_url, page_name)
            save_to_csv(products, f"{page_name}.csv")
        return

    if options is not None:
        with webdriver.Chrome(options=options) as local_driver:
            set_driver(local_driver)
            for page_name, page_url in PAGES.items():
                products = scrape_page(page_url, page_name)
                save_to_csv(products, f"{page_name}.csv")
    else:
        with webdriver.Chrome() as local_driver:
            set_driver(local_driver)
            for page_name, page_url in PAGES.items():
                products = scrape_page(page_url, page_name)
                save_to_csv(products, f"{page_name}.csv")


if __name__ == "__main__":
    get_all_products()
