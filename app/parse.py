import logging
import time
from dataclasses import dataclass
from typing import Optional
from urllib.parse import urljoin
import csv
from selenium import webdriver
from selenium.common import (
    TimeoutException,
    NoSuchElementException,
    StaleElementReferenceException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from webdriver_manager.chrome import ChromeDriverManager
from tqdm import tqdm

# Base URL for the test e-commerce site
BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")


@dataclass
class Product:
    """
    Data structure representing a single product with all required fields.
    """
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


def parse_product_element(el: WebElement) -> Product:
    """
    Extracts product details from a single product HTML container.

    Args:
        el: Selenium WebElement that wraps a single product's information.

    Returns:
        A Product instance with parsed data (title, description, price, rating, reviews).
    """
    title = (
        el.find_element(By.CLASS_NAME, "title").get_attribute("title").strip()
    )
    description = el.find_element(By.CLASS_NAME, "description").text.strip()
    price = float(el.find_element(By.CLASS_NAME, "price").text.strip().replace("$", ""))
    rating = len(el.find_elements(By.CLASS_NAME, "glyphicon-star"))  # Count star icons

    # Extract review count from <p> tags inside the ratings section
    try:
        reviews_elements = el.find_element(By.CLASS_NAME, "ratings").find_elements(By.TAG_NAME, "p")
        if len(reviews_elements) > 1:
            reviews_text = reviews_elements[1].text.strip()
            parts = reviews_text.split(" ")
            num_of_reviews = int(parts[0]) if parts[0].isdigit() else 0
        else:
            num_of_reviews = 0
    except NoSuchElementException:
        num_of_reviews = 0

    return Product(title, description, price, rating, num_of_reviews)


def accept_cookies_if_needed(driver: WebDriver) -> None:
    """
    Attempts to detect and accept cookie consent banners on the page.

    Args:
        driver: Selenium WebDriver instance currently active.
    """
    selectors = [
        (By.CLASS_NAME, "cookie-consent__agree"),
        (By.CLASS_NAME, "acceptCookies"),
    ]

    # Try each known selector to find and click the accept button
    for by, value in selectors:
        try:
            btn = WebDriverWait(driver, 5).until(ec.element_to_be_clickable((by, value)))
            btn.click()
            # Wait for the popup to disappear before continuing
            WebDriverWait(driver, 5).until(ec.invisibility_of_element_located((by, value)))
            logging.info(f"Accepted cookies using selector: {value}")
            break
        except TimeoutException:
            continue


def find_more_button(driver: WebDriver) -> Optional[WebElement]:
    """
    Tries to find the "More" button that dynamically loads additional products.

    Args:
        driver: Selenium WebDriver instance.

    Returns:
        WebElement if found, otherwise None.
    """
    try:
        return WebDriverWait(driver, 3).until(
            ec.element_to_be_clickable((By.CLASS_NAME, "ecomerce-items-scroll-more"))
        )
    except TimeoutException:
        try:
            # Try alternative button by matching the button's visible text
            return WebDriverWait(driver, 3).until(
                ec.element_to_be_clickable((By.XPATH, "//button[contains(., 'More')]"))
            )
        except TimeoutException:
            logging.warning("Pagination button not found by class or text.")
            return None


def scroll_and_load_all(driver: WebDriver, max_retries: int = 3, wait_after_click: float = 1.0) -> None:
    """
    Keeps clicking the "More" button to load all product items on the page.

    Args:
        driver: Selenium WebDriver.
        max_retries: Number of retry attempts if button is stale or fails to click.
        wait_after_click: Wait time after each click (in seconds).
    """
    while True:
        btn = find_more_button(driver)
        if not btn:
            # No more buttons to click — all products are likely loaded
            break

        retries = 0
        while retries < max_retries:
            try:
                btn.click()
                time.sleep(wait_after_click)  # Wait for new content to finish loading
                break
            except (StaleElementReferenceException, TimeoutException) as e:
                logging.warning(f"Click attempt {retries + 1} failed: {e}")
                retries += 1
                time.sleep(0.5)
                btn = find_more_button(driver)  # Re-find button in case it changed
        else:
            logging.warning("Max retries reached while trying to click the load more button.")
            break


def scrape_page(
        driver: WebDriver,
        url: str,
        filename: str,
        use_more_button: bool = False
) -> None:
    """
    Navigates to the page, optionally loads all items, and writes product data to a CSV.

    Args:
        driver: Active Selenium WebDriver instance.
        url: URL of the product category page.
        filename: CSV file where results will be saved.
        use_more_button: Whether the page has a "More" button to load extra products.
    """
    driver.get(url)  # Navigate to the target URL

    accept_cookies_if_needed(driver)  # Handle cookie consent popup if present

    # Attempt to dismiss cookie overlays if still present
    try:
        WebDriverWait(driver, 5).until(
            ec.invisibility_of_element_located((By.CLASS_NAME, "acceptCookies"))
        )
    except TimeoutException:
        pass

    if use_more_button:
        scroll_and_load_all(driver)

    # Ensure all product thumbnails are loaded
    WebDriverWait(driver, 10).until(
        ec.presence_of_all_elements_located((By.CLASS_NAME, "thumbnail"))
    )

    # Find all product containers on the page
    products = driver.find_elements(By.CLASS_NAME, "thumbnail")
    result = []

    # Parse each product card and store its info
    for element in tqdm(products, desc=f"Scraping {filename}"):
        try:
            product = parse_product_element(
                element
            )  # Parse product info from element
            result.append(product)  # Add parsed product to results list
        except Exception as e:
            logging.warning(f"Failed to parse product: {e}")
            continue

    logging.info(f"Total products scraped for {filename}: {len(result)}")

    # Write product data to CSV
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            ["title", "description", "price", "rating", "num_of_reviews"]
        )
        for product in result:
            writer.writerow(
                [
                    product.title,
                    product.description,
                    product.price,
                    product.rating,
                    product.num_of_reviews
                ]
            )


def get_all_products() -> None:
    """
    Entry point for scraping all categories.

    Sets up the headless browser, navigates to each target category page,
    and saves extracted product info to separate CSV files.
    """
    options = Options()
    options.add_argument("--headless")  # Run without browser window
    options.add_argument("--disable-gpu")  # Disable GPU (improves stability)
    options.add_argument("--no-sandbox")  # Required for some Linux environments

    # Setup ChromeDriver service with webdriver-manager for automatic driver management
    service = Service(ChromeDriverManager().install())
    driver = None

    # Setup error logging
    logging.basicConfig(level=logging.ERROR)  # Only show errors/warnings

    try:
        # Define which pages to scrape:
        driver = webdriver.Chrome(service=service, options=options)
        pages = [
            ("home", HOME_URL, False),
            ("computers", urljoin(HOME_URL, "computers"), False),
            ("laptops", urljoin(HOME_URL, "computers/laptops"), True),
            ("tablets", urljoin(HOME_URL, "computers/tablets"), True),
            ("phones", urljoin(HOME_URL, "phones"), False),
            ("touch", urljoin(HOME_URL, "phones/touch"), True),
        ]

        # Scrape all defined pages
        for name, url, use_more in pages:
            try:
                scrape_page(driver, url, f"{name}.csv", use_more_button=use_more)
            except Exception as e:
                logging.error(f"Error processing page {url}: {e}", exc_info=True)
    finally:
        if driver is not None:
            driver.quit()  # Cleanly close browser


if __name__ == "__main__":
    get_all_products()
