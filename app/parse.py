from dataclasses import dataclass, fields
from urllib.parse import urljoin
import csv
import re
import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.common.exceptions import (
    NoSuchElementException,
    TimeoutException,
    ElementClickInterceptedException,
    StaleElementReferenceException,
)
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from webdriver_manager.chrome import ChromeDriverManager


BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")
COMPUTERS_URL = urljoin(HOME_URL, "computers/")
LAPTOPS_URL = urljoin(COMPUTERS_URL, "laptops")
TABLETS_URL = urljoin(COMPUTERS_URL, "tablets")
PHONES_URL = urljoin(HOME_URL, "phones/")
TOUCHSCREEN_URL = urljoin(PHONES_URL, "touch")


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


PRODUCT_FIELDS = [field.name for field in fields(Product)]


def setup_driver(headless: bool = True,
                 implicit_wait: int = 10) -> webdriver.Chrome:
    """Setup Chrome WebDriver with optimized options."""
    options = webdriver.ChromeOptions()
    if headless:
        options.add_argument("--headless=new")
        options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    service = ChromeService(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.implicitly_wait(implicit_wait)
    return driver


def handle_cookie_banner(driver) -> None:
    """Close cookie banner if present."""
    try:
        cookie_btn = WebDriverWait(driver, 3).until(
            ec.element_to_be_clickable((By.CLASS_NAME, "acceptCookies"))
        )
        cookie_btn.click()
        time.sleep(0.5)
        print("    Cookie banner accepted")
    except (TimeoutException, NoSuchElementException):
        pass  # No cookie banner present


def _safe_find_text(el, by, selector, default=""):
    """Safely find and extract text from element."""
    try:
        sub = el.find_element(by, selector)
        return sub.text.strip()
    except NoSuchElementException:
        return default


def parse_product_element(el) -> Product:
    """Parse a single product element and extract all data."""
    # Extract title
    title_el = el.find_element(By.CSS_SELECTOR, "a.title")
    title = (title_el.get_attribute("title") or title_el.text).strip()

    # Extract description
    description = _safe_find_text(el, By.CSS_SELECTOR, "p.description", "")

    # Extract and parse price
    price_text = _safe_find_text(el, By.CSS_SELECTOR, ".price", "0")
    price_match = re.search(r"[\d.]+", price_text)
    price = float(price_match.group(0)) if price_match else 0.0

    # Count star ratings
    rating = len(el.find_elements(By.CSS_SELECTOR, ".ws-icon-star"))

    # Extract number of reviews
    num_reviews_text = _safe_find_text(
        el, By.CSS_SELECTOR, ".ratings .pull-right", ""
    )
    review_match = re.search(r"(\d+)", num_reviews_text)
    num_reviews = int(review_match.group(1)) if review_match else 0

    return Product(title, description, price, rating, num_reviews)


def load_all_products_with_more_button(driver) -> int:
    """
    Click the 'More' button repeatedly until all products are loaded.
    """
    print("    Starting pagination...")
    clicks = 0
    max_clicks = 150
    no_change_count = 0
    previous_count = 0

    while clicks < max_clicks:
        # Get current product count
        current_products = driver.find_elements(By.CSS_SELECTOR, ".thumbnail")
        current_count = len(current_products)

        # Check if count hasn't changed (indicates we're done or stuck)
        if current_count == previous_count and clicks > 0:
            no_change_count += 1
            if no_change_count >= 3:
                print(
                    f"Product count stable at {current_count} "
                    + "after {clicks} clicks"
                )
                break
        else:
            no_change_count = 0

        previous_count = current_count

        # Look for the More button
        more_btn = None

        try:
            # Wait for button to be present and visible
            more_btn = WebDriverWait(driver, 2).until(
                ec.presence_of_element_located(
                    (By.CSS_SELECTOR, "button.btn-primary, a.btn-primary")
                )
            )

            # Check if it's visible and enabled
            if not more_btn.is_displayed() or not more_btn.is_enabled():
                print(f"    More button not available after {clicks} clicks")
                break

        except TimeoutException:
            print(f"    No More button found after {clicks} clicks")
            break

        try:
            # Scroll to button with offset to avoid header overlap
            driver.execute_script(
                "arguments[0].scrollIntoView("
                + "{block: 'center', behavior: 'smooth'});",
                more_btn,
            )
            time.sleep(0.5)

            # Wait for button to be clickable
            WebDriverWait(driver, 5).until(
                ec.element_to_be_clickable(more_btn)
            )

            # Try to click
            try:
                more_btn.click()
            except (ElementClickInterceptedException,
                    StaleElementReferenceException):
                # Use JavaScript click as fallback
                driver.execute_script("arguments[0].click();", more_btn)

            clicks += 1

            # Wait for new products to load
            time.sleep(1)

            # Verify products increased
            new_count = len(
                driver.find_elements(By.CSS_SELECTOR, ".thumbnail")
            )
            if new_count > current_count:
                print(f"Click {clicks}: {current_count} -> "
                      + "{new_count} products")

        except Exception as e:
            print(f"    Error on click {clicks}: {type(e).__name__}")
            break

    final_count = len(driver.find_elements(By.CSS_SELECTOR, ".thumbnail"))
    print(f"    Pagination complete: {final_count} products loaded")
    return final_count


def collect_products_from_page(
    driver, url: str, use_more_button: bool = False
) -> list[Product]:
    """
    Navigate to URL and scrape all products.
    """
    print(f"    Navigating to {url}")
    driver.get(url)

    # Handle cookie banner on first page load
    handle_cookie_banner(driver)

    # Wait for initial page load
    wait = WebDriverWait(driver, 20)
    try:
        wait.until(
            ec.presence_of_element_located(
                (By.CSS_SELECTOR, ".thumbnail")
            )
        )
    except TimeoutException:
        print("ERROR: Page didn't load or no products found")
        return []

    # Give page time to initialize
    time.sleep(1)

    # Load all products if pagination is needed
    if use_more_button:
        load_all_products_with_more_button(driver)
        time.sleep(1)  # Final wait for all elements to render

    # Get all product elements
    product_elements = driver.find_elements(By.CSS_SELECTOR, ".thumbnail")
    print(f"    Parsing {len(product_elements)} products...")

    # Parse each product
    products = []
    for idx, el in enumerate(product_elements):
        try:
            product = parse_product_element(el)
            products.append(product)
        except Exception as e:
            print(f"    WARNING: Failed to parse product {idx + 1}: {e}")

    print(f"    Successfully parsed {len(products)} products")
    return products


def save_products_to_csv(products: list[Product], filename: str) -> None:
    """Save products to CSV file."""
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(PRODUCT_FIELDS)
        for product in products:
            writer.writerow(
                [
                    product.title,
                    product.description,
                    str(product.price),
                    str(product.rating),
                    str(product.num_of_reviews),
                ]
            )
    print(f"    Saved to {filename}")


def get_all_products() -> None:
    """
    Main scraper: scrapes all 6 pages and saves to CSV files.
    """
    pages = [
        (HOME_URL, "home.csv", False),
        (COMPUTERS_URL, "computers.csv", False),
        (LAPTOPS_URL, "laptops.csv", True),
        (TABLETS_URL, "tablets.csv", True),
        (PHONES_URL, "phones.csv", False),
        (TOUCHSCREEN_URL, "touch.csv", True),
    ]

    driver = setup_driver(headless=True)

    try:
        print("\n" + "=" * 70)
        print("STARTING E-COMMERCE SCRAPER")
        print("=" * 70)

        results = {}

        for url, filename, use_more in pages:
            print(f"\n[{filename}]")

            try:
                products = collect_products_from_page(driver, url, use_more)
                save_products_to_csv(products, filename)
                results[filename] = len(products)
            except Exception as e:
                print(f"    ERROR: {e}")
                results[filename] = 0

        # Print summary
        print("\n" + "=" * 70)
        print("SCRAPING SUMMARY")
        print("=" * 70)
        for filename, count in results.items():
            status = "✓" if count > 0 else "✗"
            print(f"  {status} {filename}: {count} products")
        print(f"  TOTAL: {sum(results.values())} products")
        print("=" * 70 + "\n")

    finally:
        driver.quit()


if __name__ == "__main__":
    get_all_products()
