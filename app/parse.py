from dataclasses import dataclass, asdict
from urllib.parse import urljoin
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.common.exceptions import TimeoutException
import csv
import time


BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


def setup_driver(headless=True):
    """Setup Chrome driver with options"""
    options = webdriver.ChromeOptions()
    if headless:
        options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(options=options)
    return driver


def accept_cookies(driver):
    """Click accept cookies button if it appears"""
    try:
        cookie_btn = WebDriverWait(driver, 3).until(
            ec.element_to_be_clickable((By.CLASS_NAME, "acceptCookies"))
        )
        cookie_btn.click()
        time.sleep(1)
    except TimeoutException:
        pass  # No cookie banner


def load_all_products(driver):
    """Click 'More' button until all products are loaded"""
    while True:
        try:
            more_button = WebDriverWait(driver, 3).until(
                ec.element_to_be_clickable(
                    (By.CLASS_NAME, "ecomerce-items-scroll-more")
                )
            )
            more_button.click()
            time.sleep(1)
        except TimeoutException:
            break


def parse_product(product_element):
    """Parse a single product element"""
    try:
        title_element = product_element.find_element(
            By.CLASS_NAME, "title"
        )
        title = title_element.get_attribute("title")
        description = product_element.find_element(
            By.CLASS_NAME, "description"
        ).text
        price_text = product_element.find_element(
            By.CLASS_NAME, "price"
        ).text
        price = float(price_text.replace("$", ""))

        rating = len(product_element.find_elements(
            By.CSS_SELECTOR, ".ratings .ws-icon-star")
        )

        reviews_text = product_element.find_element(
            By.CLASS_NAME, "ratings"
        ).find_element(By.TAG_NAME, "p").text
        num_reviews = int(reviews_text.split()[0])

        return Product(title, description, price, rating, num_reviews)
    except Exception as e:
        print(f"Error parsing product: {e}")
        return None


def scrape_page(url, output_file):
    """Scrape a single page and save to CSV"""
    driver = setup_driver(headless=False)
    products = []

    try:
        driver.get(url)
        accept_cookies(driver)
        load_all_products(driver)

        product_elements = driver.find_elements(
            By.CLASS_NAME, "thumbnail"
        )

        for element in product_elements:
            product = parse_product(element, driver)
            if product:
                products.append(product)

        save_to_csv(products, output_file)
        print(f"Scraped {len(products)} products from {url}")

    finally:
        driver.quit()

    return products


def save_to_csv(products, filename):
    """Save products to CSV file"""
    if not products:
        return

    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, fieldnames=["title", "description", "price", "rating", "num_of_reviews"]
        )
        writer.writeheader()
        for product in products:
            writer.writerow(asdict(product))


def get_all_products():
    """Main function to scrape all pages"""
    pages = [
        (
            "https://webscraper.io/test-sites/e-commerce/more",
            "home.csv"
        ),
        (
            "https://webscraper.io/test-sites/e-commerce/more/computers",
            "computers.csv"
        ),
        (
            "https://webscraper.io/test-sites/e-commerce/more/computers/laptops",
            "laptops.csv"
        ),
        (
            "https://webscraper.io/test-sites/e-commerce/more/computers/tablets",
            "tablets.csv"
        ),
        (
            "https://webscraper.io/test-sites/e-commerce/more/phones",
            "phones.csv"
        ),
        (
            "https://webscraper.io/test-sites/e-commerce/more/phones/touch",
            "touch.csv"
        ),
    ]

    for url, output_file in pages:
        scrape_page(url, output_file)


if __name__ == "__main__":
    get_all_products()
