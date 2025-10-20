import csv
import time
from dataclasses import dataclass
from urllib.parse import urljoin

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from tqdm import tqdm

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
    return _driver


def set_driver(new_driver: webdriver.Chrome) -> None:
    global _driver
    _driver = new_driver


def accept_cookies() -> None:
    driver = get_driver()
    try:
        accept_button = WebDriverWait(driver, 3).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, ".acceptCookies"))
        )
        accept_button.click()
        time.sleep(1)
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
    title_element = product_element.find_element(By.CLASS_NAME, "title")
    title = title_element.get_attribute("title")

    description = product_element.find_element(
        By.CLASS_NAME, "description"
    ).text.strip()

    price_text = product_element.find_element(By.CLASS_NAME, "price").text.strip()
    price = float(price_text.replace("$", ""))

    reviews_element = product_element.find_element(By.CLASS_NAME, "ratings")
    rating_stars = reviews_element.find_elements(By.CLASS_NAME, "ws-icon-star")
    rating = len(rating_stars)

    review_count_text = reviews_element.find_element(
        By.CLASS_NAME, "review-count"
    ).text.strip()
    num_of_reviews = int(review_count_text.split()[0])

    return Product(
        title=title,
        description=description,
        price=price,
        rating=rating,
        num_of_reviews=num_of_reviews,
    )


def load_all_products_on_page() -> None:
    driver = get_driver()
    while True:
        try:
            more_button = WebDriverWait(driver, 2).until(
                EC.element_to_be_clickable(
                    (By.CLASS_NAME, "ecomerce-items-scroll-more")
                )
            )
            more_button.click()
            time.sleep(1)
        except (TimeoutException, NoSuchElementException):
            break


def scrape_page(url: str, page_name: str) -> list[Product]:
    driver = get_driver()
    driver.get(url)

    accept_cookies()

    load_all_products_on_page()

    product_elements = driver.find_elements(By.CLASS_NAME, "thumbnail")

    products = []
    for element in tqdm(
        product_elements, desc=f"Scraping {page_name.capitalize()} page", unit="product"
    ):
        product = parse_product(element)
        products.append(product)

    return products


def save_to_csv(products: list[Product], filename: str) -> None:
    with open(filename, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["title", "description", "price", "rating", "num_of_reviews"])
        for product in products:
            writer.writerow(
                [
                    product.title,
                    product.description,
                    product.price,
                    product.rating,
                    product.num_of_reviews,
                ]
            )


def get_all_products() -> None:
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")

    with webdriver.Chrome(options=options) as driver:
        set_driver(driver)

        for page_name, page_url in PAGES.items():
            products = scrape_page(page_url, page_name)
            save_to_csv(products, f"{page_name}.csv")


if __name__ == "__main__":
    get_all_products()
