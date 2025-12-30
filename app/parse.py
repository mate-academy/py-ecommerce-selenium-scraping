import csv
import time
from dataclasses import dataclass, fields
from typing import List, Dict

from tqdm import tqdm  # Optional task #2
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException

# Setup URL constants
BASE_URL = "https://webscraper.io/test-sites/e-commerce/more"

# Define the pages to scrape and their URL suffixes
PAGES = {
    "home": "",
    "computers": "/computers",
    "laptops": "/computers/laptops",
    "tablets": "/computers/tablets",
    "phones": "/phones",
    "touch": "/phones/touch"
}

@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int

def get_driver():
    """Initializes and returns a Selenium WebDriver with Headless options."""
    options = Options()
    options.add_argument("--headless")  # Optional task #1
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-blink-features=AutomationControlled")
    
    # Initialize the driver (ensure you have chromedriver in PATH or use webdriver-manager)
    driver = webdriver.Chrome(options=options)
    return driver

def accept_cookies(driver) -> None:
    """Checks for the cookie banner and accepts it if present."""
    try:
        # Wait briefly for the cookie banner
        accept_button = WebDriverWait(driver, 3).until(
            EC.element_to_be_clickable((By.CLASS_NAME, "acceptCookies"))
        )
        accept_button.click()
    except TimeoutException:
        # Cookies banner didn't appear or was already accepted
        pass

def write_to_csv(filename: str, products: List[Product]) -> None:
    """Writes a list of Product objects to a CSV file."""
    if not products:
        return

    with open(f"{filename}.csv", mode="w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        # Write header based on dataclass fields
        header = [field.name for field in fields(Product)]
        writer.writerow(header)
        
        # Write rows
        for product in products:
            writer.writerow([
                product.title,
                product.description,
                product.price,
                product.rating,
                product.num_of_reviews
            ])

def extract_product_data(product_element) -> Product:
    """Parses a single WebElement to create a Product object."""
    title = product_element.find_element(By.CLASS_NAME, "title").get_attribute("title")
    price_str = product_element.find_element(By.CLASS_NAME, "price").text
    description = product_element.find_element(By.CLASS_NAME, "description").text
    
    # Rating is often hidden in class names or attributes (e.g., "rating-4")
    # For this specific site, we count the stars
    ratings = product_element.find_elements(By.CSS_SELECTOR, ".ratings .glyphicon-star")
    rating = len(ratings)
    
    reviews_text = product_element.find_element(By.ClassName, "ratings").text
    # Usually format is "X reviews", extract just the number
    num_of_reviews = int(reviews_text.split()[0])
    
    # Clean price string ($123.45 -> 123.45)
    price = float(price_str.replace("$", ""))

    return Product(
        title=title,
        description=description,
        price=price,
        rating=rating,
        num_of_reviews=num_of_reviews
    )

def scrape_single_page(driver, url_suffix: str) -> List[Product]:
    """
    Global logic for parsing a single page including pagination ("More" button).
    """
    full_url = f"{BASE_URL}{url_suffix}"
    driver.get(full_url)
    
    # Handle cookies once per page load to be safe
    accept_cookies(driver)

    # --- Pagination Logic ---
    while True:
        try:
            # Locate the "More" button
            more_button = driver.find_element(By.CLASS_NAME, "ecomerce-items-scroll-more")
            
            # If button is hidden (style="display: none"), break the loop
            if not more_button.is_displayed():
                break

            # Click the button
            more_button.click()
            
            # Wait for new products to load. 
            # We wait until the specific loading spinner/wrapper is gone or count increases.
            # A simple sleep is often stable enough for this test site, 
            # but WebDriverWait is better practice.
            time.sleep(0.5) 
            
        except (NoSuchElementException, ElementClickInterceptedException):
            # Button doesn't exist or we reached the end
            break
        except Exception:
            # Safety break to prevent infinite loops on errors
            break

    # --- Data Extraction ---
    # After pagination is done, all elements are in the DOM. 
    # We collect them now to avoid StaleElementReferenceExceptions.
    product_elements = driver.find_elements(By.CLASS_NAME, "thumbnail")
    
    products = []
    for element in product_elements:
        products.append(extract_product_data(element))
        
    return products

def get_all_products():
    """Main execution function."""
    driver = get_driver()
    
    try:
        # Optional Task #2: Using tqdm for a progress bar
        iterator = tqdm(PAGES.items(), desc="Scraping Pages")
        
        for page_name, url_suffix in iterator:
            products = scrape_single_page(driver, url_suffix)
            write_to_csv(page_name, products)
            
    finally:
        driver.quit()

if __name__ == "__main__":
    get_all_products()
