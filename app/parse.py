from dataclasses import dataclass
from typing import List

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from urllib.parse import urljoin
import csv
import time

from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait
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


def get_driver() -> webdriver.Chrome:
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    return webdriver.Chrome(options=options)


def accept_cookies(driver: webdriver.Chrome) -> None:
    try:
        accept_button = WebDriverWait(driver, 5).until(
            expected_conditions.element_to_be_clickable(
                (By.CLASS_NAME, "acceptCookies")
            )
        )
        accept_button.click()
    except Exception:
        pass


def parse_product_element(element: WebElement) -> Product:
    title = element.find_element(By.CLASS_NAME, "title").get_attribute("title")
    description = element.find_element(By.CLASS_NAME, "description").text
    price_text = element.find_element(
        By.CLASS_NAME, "price"
    ).text.replace("$", "").strip()
    price = float(price_text) if price_text else 0.0

    rating_container = element.find_element(By.CLASS_NAME, "ratings")
    stars = rating_container.find_elements(By.CLASS_NAME, "ws-icon-star")
    rating = len(stars)

    review_text = element.find_element(
        By.CLASS_NAME, "review-count"
    ).text.split()[0]
    num_of_reviews = int(review_text) if review_text.isdigit() else 0

    return Product(title, description, price, rating, num_of_reviews)


def parse_products_from_page(driver: webdriver.Chrome) -> List[Product]:
    elements = driver.find_elements(By.CLASS_NAME, "thumbnail")
    return [parse_product_element(el) for el in elements]


def click_more_buttons(driver: webdriver.Chrome) -> None:
    while True:
        try:
            button = WebDriverWait(driver, 3).until(
                expected_conditions.element_to_be_clickable(
                    (By.CLASS_NAME, "btn-primary")
                )
            )
            driver.execute_script("arguments[0].click();", button)
            time.sleep(1)
        except Exception:
            break


def save_products_to_csv(products: List[Product], filename: str) -> None:
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            ["title", "description", "price", "rating", "num_of_reviews"]
        )
        for prod in products:
            writer.writerow(
                [
                    prod.title,
                    prod.description,
                    prod.price,
                    prod.rating,
                    prod.num_of_reviews
                ]
            )


def process_page(
        driver: webdriver.Chrome,
        url: str,
        filename: str,
        use_more_button: bool = False
) -> None:
    driver.get(url)
    accept_cookies(driver)

    if use_more_button:
        click_more_buttons(driver)

    products = parse_products_from_page(driver)
    save_products_to_csv(products, filename)


def get_all_products() -> None:
    urls = [
        (HOME_URL, "home.csv", False),
        (urljoin(HOME_URL, "computers"), "computers.csv", False),
        (urljoin(HOME_URL, "computers/laptops"), "laptops.csv", True),
        (urljoin(HOME_URL, "computers/tablets"), "tablets.csv", True),
        (urljoin(HOME_URL, "phones"), "phones.csv", False),
        (urljoin(HOME_URL, "phones/touch"), "touch.csv", True),
    ]

    driver = get_driver()
    try:
        for url, filename, use_more in tqdm(urls, desc="Processing pages"):
            process_page(driver, url, filename, use_more)
    finally:
        driver.quit()


if __name__ == "__main__":
    get_all_products()