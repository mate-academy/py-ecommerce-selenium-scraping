import csv
import time
from dataclasses import dataclass, fields, astuple
from urllib.parse import urljoin
from typing import Generator

from selenium import webdriver
from selenium.common.exceptions import (
    NoSuchElementException,
    ElementClickInterceptedException
)
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from tqdm import tqdm

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")

PAGES = {
    "home": HOME_URL,
    "computers": f"{BASE_URL}test-sites/e-commerce/more/computers",
    "laptops": f"{BASE_URL}test-sites/e-commerce/more/computers/laptops",
    "tablets": f"{BASE_URL}test-sites/e-commerce/more/computers/tablets",
    "phones": f"{BASE_URL}test-sites/e-commerce/more/phones",
    "touch": f"{BASE_URL}test-sites/e-commerce/more/phones/touch",
}


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int

    def __post_init__(self) -> None:
        try:
            self.price = float(self.price)
            self.rating = int(self.rating)
            self.num_of_reviews = int(self.num_of_reviews)
        except ValueError:
            # это header — оставляем как есть
            pass


def get_driver() -> WebDriver:
    """Create and return a headless Chrome WebDriver instance."""
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    return webdriver.Chrome(options=options)


def accept_cookies(driver: WebDriver) -> None:
    """Click the 'Accept Cookies' button if it appears on the page."""
    try:
        cookie_btn = driver.find_element(By.CLASS_NAME, "acceptCookies")
        cookie_btn.click()
        time.sleep(0.5)
    except NoSuchElementException:
        pass


def load_all_products(driver: WebDriver) -> None:
    """
    Click the 'More' button repeatedly until it disappears,
    loading all paginated products onto the page.
    """
    while True:
        try:
            more_btn = driver.find_element(
                By.CLASS_NAME, "ecomerce-items-scroll-more"
            )
            if not more_btn.is_displayed():
                break
            # more_btn.click()
            # time.sleep(1.8)  # Wait for new items to render
            driver.execute_script("arguments[0].click();", more_btn)
            time.sleep(2)

        except (NoSuchElementException, ElementClickInterceptedException):
            break


def parse_product(card: WebElement) -> Product:
    """Extract product data from a single product card WebElement."""
    title = card.find_element(
        By.CSS_SELECTOR, "a.title"
    ).get_attribute("title")
    description = card.find_element(
        By.CSS_SELECTOR, "p.description"
    ).text
    price = float(
        card.find_element(By.CSS_SELECTOR, "h4.price").text.replace("$", "")
    )
    stars = card.find_elements(By.CSS_SELECTOR, "span.ws-icon-star")
    rating = len(stars)
    reviews_text = card.find_element(By.CSS_SELECTOR, "p.review-count").text
    num_of_reviews = int(reviews_text.split()[0])

    return Product(
        title=title,
        description=description,
        price=price,
        rating=rating,
        num_of_reviews=num_of_reviews,
    )


def scrape_page(driver: WebDriver, url: str) -> Generator[Product, None, None]:
    """
    Navigate to a URL, handle cookies, expand all paginated content,
    and yield Product instances for each product card found.
    """
    driver.get(url)
    time.sleep(1.5)  # Let the page fully load before interacting
    accept_cookies(driver)
    load_all_products(driver)

    cards = driver.find_elements(By.CSS_SELECTOR, "div.product-wrapper")
    # temporary debug statement
    # print(f"\nFound {len(cards)} products on {url}")
    for card in cards:
        yield parse_product(card)


def save_to_csv(products: list[Product], filename: str) -> None:
    """Write a list of Product instances to a CSV file."""
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([field.name for field in fields(Product)])
        writer.writerows(astuple(p) for p in products)


def get_all_products() -> None:
    """
    Main entry point: scrape all configured pages and save each
    to a corresponding .csv file.
    """
    driver = get_driver()

    try:
        for page_name, url in tqdm(PAGES.items(), desc="Scraping pages"):
            # print(f"Scraping {page_name} : {url}...")
            products = list(scrape_page(driver, url))
            save_to_csv(products, f"{page_name}.csv")
            tqdm.write(f"  ✓ {page_name}.csv — {len(products)} products saved")
    finally:
        driver.quit()


if __name__ == "__main__":
    get_all_products()
