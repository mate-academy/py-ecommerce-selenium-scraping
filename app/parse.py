import csv
from dataclasses import dataclass, astuple
from urllib.parse import urljoin

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
)


BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


def setup_driver() -> webdriver.Chrome:
    """Create Selenium Chrome driver in headless mode."""
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-blink-features=AutomationControlled")

    driver = webdriver.Chrome(options=options)
    driver.implicitly_wait(5)
    return driver

def accept_cookies(driver: webdriver.Chrome) -> None:
    """Click Accept Cookies button if it appears."""
    try:
        button = WebDriverWait(driver, 3).until(
            EC.element_to_be_clickable((By.ID, "cookieBannerButton"))
        )
        button.click()
    except TimeoutException:
        # Cookie banner did not appear
        pass

def parse_products_on_page(driver: webdriver.Chrome) -> list[Product]:
    """Parse all products currently visible on page."""
    products = []

    cards = driver.find_elements(By.CLASS_NAME, "thumbnail")

    for card in cards:
        title = card.find_element(By.CLASS_NAME, "title").get_attribute("title")
        description = card.find_element(By.CLASS_NAME, "description").text

        price_text = card.find_element(By.CLASS_NAME, "price").text
        price = float(price_text.replace("$", ""))

        rating = len(card.find_elements(By.CLASS_NAME, "ws-icon-star"))

        reviews_text = card.find_element(By.CLASS_NAME, "review-count").text
        num_of_reviews = int(reviews_text.split()[0])

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

def load_all_products_from_category(
    driver: webdriver.Chrome,
    url: str,
) -> list[Product]:
    """
    Load all products from category including pagination via 'More' button.
    """
    driver.get(url)
    accept_cookies(driver)

    # Click "More" button until it disappears
    while True:
        try:
            more_button = driver.find_element(By.CSS_SELECTOR, "button.btn.btn-primary")

            if more_button.is_displayed():
                driver.execute_script("arguments[0].click();", more_button)

                # Wait until previous button becomes stale (page updated)
                WebDriverWait(driver, 5).until(
                    EC.staleness_of(more_button)
                )
            else:
                break

        except NoSuchElementException:
            # No more button → all products loaded
            break

    # Parse only once after all products loaded
    return parse_products_on_page(driver)

def save_to_csv(filename: str, products: list[Product]) -> None:
    """Save list of products to CSV file."""
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(Product.__annotations__.keys())
        writer.writerows([astuple(product) for product in products])


def get_all_products() -> None:
    driver = setup_driver()

    pages = {
        "home.csv": HOME_URL,
        "computers.csv": urljoin(HOME_URL, "computers"),
        "laptops.csv": urljoin(HOME_URL, "computers/laptops"),
        "tablets.csv": urljoin(HOME_URL, "computers/tablets"),
        "phones.csv": urljoin(HOME_URL, "phones"),
        "touch.csv": urljoin(HOME_URL, "phones/touch"),
    }

    try:
        for filename, url in pages.items():
            products = load_all_products_from_category(driver, url)
            save_to_csv(filename, products)
    finally:
        driver.quit()

if __name__ == "__main__":
    get_all_products()
