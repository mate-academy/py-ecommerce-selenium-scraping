import csv
import requests
import time
from tqdm import tqdm
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import ElementNotInteractableException
from dataclasses import dataclass, astuple
from urllib.parse import urljoin

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")
COMPUTERS_URL = urljoin(HOME_URL, "computers/")
LAPTOPS_URL = urljoin(COMPUTERS_URL, "laptops")
TABLETS_URL = urljoin(COMPUTERS_URL, "tablets")
PHONES_URL = urljoin(HOME_URL, "phones/")
TOUCH_URL = urljoin(PHONES_URL, "touch")

# A dictionary mapping filenames to URLs for easier looping
URL_SCRAPE_DICT = {
    "laptops": LAPTOPS_URL,
    "tablets": TABLETS_URL,
    "touch": TOUCH_URL,
    "home": HOME_URL,
    "computers": COMPUTERS_URL,
    "phones": PHONES_URL,
}

# Define product fields for CSV writing
PRODUCT_FIELDS = ["title", "description", "price", "rating", "num_of_reviews"]

# Global variable to hold the Selenium WebDriver instance
_driver: WebDriver | None = None


# Getter and setter functions for the WebDriver to allow reuse across functions
def get_driver() -> WebDriver:
    return _driver


def set_driver(new_driver: WebDriver) -> None:
    global _driver
    _driver = new_driver


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


# Function to write a list of products to a CSV file
def write_products_to_csv(products: list[Product], dwnld_path: str) -> None:
    with open(dwnld_path, "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(PRODUCT_FIELDS)
        writer.writerows([astuple(product) for product in products])


# Function to extract product details from the parsed HTML
def get_one_product(product_soup: BeautifulSoup) -> Product:
    stars = product_soup.select("p .ws-icon.ws-icon-star")
    rating = len(stars)
    return Product(
        title=product_soup.select_one(".title")["title"],
        description=product_soup.select_one(
            ".description"
        ).text.replace(u"\xa0", " "),  # Clean non-breaking spaces
        price=float(product_soup.select_one(".price ").text.replace("$", "")),
        rating=int(rating),
        num_of_reviews=int(
            product_soup.select_one(".review-count").text.split()[0]
        )
    )


# Function to handle dynamic content loading
# (clicking "Load more" button with Selenium)
def get_full_page_with_dynamic_content(url: str) -> str:
    driver = get_driver()
    driver.get(url)
    time.sleep(5)  # Wait for content to load (and accept cookies)
    while True:
        try:
            more_button = driver.find_element(
                By.CLASS_NAME, "ecomerce-items-scroll-more"
            )
            more_button.click()
        except ElementNotInteractableException:
            print(f"Load full page: {url} - complete.")
            break
    full_page = driver.page_source
    return full_page


# Function to scrape products (either statically with requests
# or dynamically with Selenium)
def get_products(url: str) -> list[Product]:
    page = requests.get(url).content
    soup = BeautifulSoup(page, "html.parser")

    # Check if the "Load more" button exists
    button_element = soup.select_one(".ecomerce-items-scroll-more")

    if button_element is not None:
        page = get_full_page_with_dynamic_content(url=url)
        soup = BeautifulSoup(page, "html.parser")

    products = soup.select(".product-wrapper")
    return [get_one_product(product) for product in products]


# Main function to loop through URLs, scrape products,
# and save them to CSV files
def get_all_products() -> None:
    with webdriver.Chrome() as new_driver:
        set_driver(new_driver)
        for filename, url in tqdm(URL_SCRAPE_DICT.items()):
            products = get_products(url)
            write_products_to_csv(products, f"{filename}.csv")


if __name__ == "__main__":
    get_all_products()
