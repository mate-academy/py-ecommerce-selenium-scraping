import logging
import os
import sys
from dataclasses import fields, dataclass, astuple
import csv
from urllib.parse import urljoin
import time
import requests
from bs4 import BeautifulSoup, Tag
from tqdm import tqdm
from selenium import webdriver
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more")
COMPUTERS_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/computers")
LAPTOPS_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/computers/laptops")
TABLETS_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/computers/tablets")
PHONES_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/phones")
TOUCH_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/phones/touch")

_driver: WebDriver | None = None


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


PRODUCT_FIELDS = [field.name for field in fields(Product)]

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)8s:  %(message)s",
    handlers=[
        logging.FileHandler("parser.log"),
        logging.StreamHandler(sys.stdout)
    ]
)


def parse_simple_product(product: Tag) -> Product:
    description = product.select_one(".card-text").text.replace("\xa0", " ")
    rating_element = product.select_one("p[data-rating]")
    rating = int(rating_element["data-rating"]) if rating_element else 5
    reviews_element = product.select_one(".review-count")
    if not reviews_element:
        reviews_element = product.select_one(".review-count.float-end.pull-right")

    num_of_reviews = int(
        reviews_element.text.replace("reviews", "").
        replace(",", "")) if reviews_element else 0

    return Product(
        title=product.select_one(".title")["title"],
        description=description,
        price=float(product.select_one(".pull-right").text.replace("$", "")),
        num_of_reviews=num_of_reviews,
        rating=rating,
    )


def get_single_page_products(page_soup: Tag) -> [Product]:
    products = page_soup.select(".card-body")
    return [parse_simple_product(product) for product in products]


def get_all_products_from_category(category_url: str) -> list[Product]:
    logging.info(f"Start parsing {category_url}")
    all_products = []
    driver = get_driver()

    try:
        driver.get(category_url)
        logging.info(f"Loaded page: {category_url}")

        try:
            cookie_button = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "acceptCookies"))
            )
            cookie_button.click()
            logging.info("Clicked the 'Accept Cookies' button.")
        except Exception as e:
            logging.warning(f"Cookie button not found or could not be clicked: {e}")

        more_button = driver.find_elements(By.CSS_SELECTOR, ".ecomerce-items-scroll-more")
        if more_button and more_button[0].get_attribute("style") != "display: none;":
            logging.info("Found the 'More' button. Clicking it to load all products...")
            while True:
                more_button[0].click()
                time.sleep(2)
                more_button = driver.find_elements(By.CSS_SELECTOR, ".ecomerce-items-scroll-more")
                if not more_button or more_button[0].get_attribute("style") == "display: none;":
                    logging.info("No more products to load. Finished clicking the 'More' button.")
                    break
        soup = BeautifulSoup(driver.page_source, "html.parser")
        current_products = get_single_page_products(soup)
        all_products.extend(current_products)
        logging.info(f"Added {len(current_products)} products from the page. Total: {len(all_products)}")

    except Exception as e:
        logging.error(f"Error occurred while parsing {category_url}: {e}")
    finally:
        logging.info(f"Finished parsing {category_url}. Found {len(all_products)} products.")
        return all_products


def write_products_to_csv(products: list[Product], filename: str) -> None:
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(PRODUCT_FIELDS)
        writer.writerows([astuple(product) for product in products])


def get_all_products() -> None:
    pages = [
        {"name": "home", "url": HOME_URL},
        {"name": "phones", "url": PHONES_URL},
        {"name": "computers", "url": COMPUTERS_URL},
        {"name": "laptops", "url": LAPTOPS_URL},
        {"name": "tablets", "url": TABLETS_URL},
        {"name": "touch", "url": TOUCH_URL},
    ]

    for page in pages:
        print(f"Processing category: {page['name']} with URL: {page['url']}")
        try:
            products = get_all_products_from_category(page["url"])
            filename = f"{page['name']}.csv"
            write_products_to_csv(products, filename)
            logging.info(f"Saved {len(products)} products to {filename}")
        except Exception as e:
            logging.error(f"Failed to process category {page['name']}. Error: {e}")


def main():
    with webdriver.Chrome() as driver:
        set_driver(driver)
        get_all_products()


if __name__ == "__main__":
    main()
