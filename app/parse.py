import csv
import time
from dataclasses import dataclass
from urllib.parse import urljoin

from selenium.common import TimeoutException, NoSuchElementException
from tqdm import tqdm

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.wait import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support import expected_conditions as EC

# Constants
ACCEPT_COOKIES_WAIT_TIME = 1

# Define the base URLs and pages to scrape
BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")

# Set up the pages to scrape
PAGES_TO_SCRAPE = {
    "home": HOME_URL,
    "computers": urljoin(HOME_URL, "computers"),
    "laptops": urljoin(HOME_URL, "computers/laptops"),
    "tablets": urljoin(HOME_URL, "computers/tablets"),
    "phones": urljoin(HOME_URL, "phones"),
    "touch": urljoin(HOME_URL, "phones/touch"),
}


# Define the Product data class
@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


# Function to click the "More" button until its display style becomes "none"
def click_more_button_until_hidden(driver):
    while True:
        try:
            more_button = driver.find_element(
                By.CLASS_NAME, "ecomerce-items-scroll-more"
            )
            if more_button.is_displayed():
                more_button.click()
                time.sleep(
                    1
                )  # Adding a short delay to allow the page to load after clicking
            else:
                break  # Exit the loop if the button is not displayed
        except NoSuchElementException:
            break  # Exit the loop if the element is not found


# Function to scrape product data from a single product element
def scrape_product_data(product_element):
    title_element = product_element.find_element(By.CLASS_NAME, "title")
    title = title_element.get_attribute("title")

    description = product_element.find_element(By.CLASS_NAME, "description").text

    price = float(
        product_element.find_element(By.CLASS_NAME, "price").text.replace("$", "")
    )

    rating_element = product_element.find_element(By.CLASS_NAME, "ratings")
    spans = rating_element.find_elements(By.TAG_NAME, "span")
    rating = len(spans)

    num_of_reviews = int(
        product_element.find_element(By.CLASS_NAME, "ratings").text.split()[0]
    )

    return Product(title, description, price, rating, num_of_reviews)


# Function to write product data to a CSV file
def write_product_data_to_csv(file_name, product_list):
    with open(f"{file_name}.csv", mode="w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["title", "description", "price", "rating", "num_of_reviews"])
        for product in product_list:
            writer.writerow(
                [
                    product.title,
                    product.description,
                    product.price,
                    product.rating,
                    product.num_of_reviews,
                ]
            )


# Function to scrape all products and write to CSV
def get_all_products():
    # Set up the WebDriver
    options = Options()
    options.add_argument("--headless")  # Run headless for testing
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()), options=options
    )

    # Initialize tqdm for progress bar
    pbar = tqdm(PAGES_TO_SCRAPE.items(), desc="Scraping Pages", unit="page")

    for file_name, url in pbar:
        pbar.set_postfix(page=file_name)

        driver.get(url)

        # Handle the "Accept Cookies" button if it appears
        try:
            accept_cookies_button = WebDriverWait(
                driver, ACCEPT_COOKIES_WAIT_TIME
            ).until(EC.element_to_be_clickable((By.CLASS_NAME, "acceptCookies")))
            accept_cookies_button.click()
        except TimeoutException:
            pass

        # Click the "More" button until its display style becomes "none"
        click_more_button_until_hidden(driver)

        # Find the product elements
        products = driver.find_elements(By.CLASS_NAME, "thumbnail")

        # List to store the product data
        product_list = []

        # Extract the required information
        for product in products:
            product_data = scrape_product_data(product)
            product_list.append(product_data)

        # Write the product data to a CSV file
        write_product_data_to_csv(file_name, product_list)

        # Update tqdm progress bar
        pbar.update()

    # Close the WebDriver
    driver.quit()


# Entry point of the script
if __name__ == "__main__":
    get_all_products()
