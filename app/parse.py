import csv
import time
from dataclasses import dataclass, fields
from typing import List
from urllib.parse import urljoin

from selenium import webdriver
from selenium.common.exceptions import (
    NoSuchElementException,
    TimeoutException,
)
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.expected_conditions import (
    element_to_be_clickable,
    presence_of_element_located,
)
from selenium.webdriver.support.ui import WebDriverWait
from tqdm import tqdm


BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")

PAGES = {
    "home": HOME_URL,
    "computers": urljoin(HOME_URL, "computers"),
    "laptops": urljoin(HOME_URL, "computers/laptops"),
    "tablets": urljoin(HOME_URL, "computers/tablets"),
    "phones": urljoin(HOME_URL, "phones"),
    "touch": urljoin(HOME_URL, "phones/touch"),
}


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


def get_driver() -> webdriver.Chrome:
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    return webdriver.Chrome(options=options)


def accept_cookies(driver: webdriver.Chrome) -> None:
    try:
        button = WebDriverWait(driver, 3).until(
            element_to_be_clickable(
                (By.CSS_SELECTOR, "[data-tid='banner-accept']")
            )
        )
        button.click()
    except TimeoutException:
        pass


def load_all_products(driver: webdriver.Chrome) -> None:
    while True:
        try:
            more_button = driver.find_element(
                By.CLASS_NAME, "ecomerce-items-scroll-more"
            )
            if not more_button.is_displayed():
                break
            driver.execute_script("arguments[0].click();", more_button)
            time.sleep(1)
        except NoSuchElementException:
            break


def parse_single_product(card: WebElement) -> Product:
    title = card.find_element(
        By.CLASS_NAME, "title"
    ).get_attribute("title")
    description = card.find_element(
        By.CLASS_NAME, "description"
    ).text
    price = float(
        card.find_element(
            By.CLASS_NAME, "price"
        ).text.replace("$", "")
    )
    stars = card.find_elements(By.CSS_SELECTOR, "span.ws-icon-star")
    rating = len(stars)
    reviews_text = card.find_element(
        By.CLASS_NAME, "review-count"
    ).text
    num_of_reviews = int(reviews_text.split()[0])
    return Product(
        title=title,
        description=description,
        price=price,
        rating=rating,
        num_of_reviews=num_of_reviews,
    )


def parse_products(driver: webdriver.Chrome) -> List[Product]:
    cards = driver.find_elements(By.CLASS_NAME, "thumbnail")
    return [parse_single_product(card) for card in cards]


def save_to_csv(products: List[Product], filename: str) -> None:
    header = [product_field.name for product_field in fields(Product)]
    with open(filename, "w", newline="", encoding="utf-8") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(header)
        for product in products:
            writer.writerow([
                product.title,
                product.description,
                product.price,
                product.rating,
                product.num_of_reviews,
            ])


def scrape_page(
    driver: webdriver.Chrome,
    url: str,
    page_name: str,
) -> None:
    driver.get(url)
    WebDriverWait(driver, 10).until(
        presence_of_element_located((By.CLASS_NAME, "thumbnail"))
    )
    accept_cookies(driver)
    load_all_products(driver)
    products = parse_products(driver)
    save_to_csv(products, f"{page_name}.csv")


def get_all_products() -> None:
    driver = get_driver()
    try:
        for page_name, url in tqdm(
            PAGES.items(), desc="Scraping pages"
        ):
            scrape_page(driver, url, page_name)
    finally:
        driver.quit()


if __name__ == "__main__":
    get_all_products()
