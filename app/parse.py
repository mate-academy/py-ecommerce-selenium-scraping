import csv
import logging
import sys
from dataclasses import dataclass, fields, astuple
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup, Tag


BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")
COMPUTERS_URL = urljoin(HOME_URL, "computers/")
LAPTOP_URL = urljoin(COMPUTERS_URL, "laptops")
TABLETS_URL = urljoin(COMPUTERS_URL, "tablets")
PHONES_URL = urljoin(HOME_URL, "phones/")
TOUCH_URL = urljoin(PHONES_URL, "touch")

ALL_URL = {
    HOME_URL: "home.csv",
    COMPUTERS_URL: "computers.csv",
    PHONES_URL: "phones.csv",
    TABLETS_URL: "tablets.csv",
    LAPTOP_URL: "laptops.csv",
    TOUCH_URL: "touch.csv",
}


_driver: webdriver.Chrome | None = None


def get_driver() -> webdriver.Chrome:
    if _driver is None:
        raise RuntimeError("Driver is not set. Call set_driver(driver) first.")
    return _driver


def set_driver(new_driver: webdriver.Chrome) -> None:
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
    level=logging.DEBUG,
    format="[%(levelname)8s]: %(message)s",
    handlers=[
        logging.FileHandler("parser.log"),
        logging.StreamHandler(sys.stdout),
    ]
)


def parse_single_product(product: Tag) -> Product:
    """Function to parse a single product. It creates class instances
    of Product from product soup"""

    title_tag = product.select_one(".title")
    description_tag = product.select_one(".description")
    price_tag = product.select_one(".price")
    review_count_tag = product.select_one("[itemprop=reviewCount]")
    star_tags = product.select("span.ws-icon-star")

    return Product(
        title=title_tag["title"] if title_tag else "",
        description=(
            description_tag.text.replace("\xa0", " ").strip()
            if description_tag
            else ""
        ),
        price=float(price_tag.text.replace("$", "")) if price_tag else 0.0,
        rating=len(star_tags),
        num_of_reviews=int(review_count_tag.text) if review_count_tag else 0
    )


def get_single_page_products(page_soup: Tag) -> list[Product]:
    """Function thet creates a list of products from a single page."""

    products = page_soup.select("div.thumbnail")
    logging.info(f"Found {len(products)} products")
    print(len(products))
    return [parse_single_product(product) for product in products]


def get_static_products(page_url: str) -> list[Product]:
    """Function that collect soup from pages without pagination or other
    dynamic properties, and calls the function that creates a list of
    [Products] from a single page."""
    logging.info(f"Static parsing: {page_url}")

    response = requests.get(page_url)
    response.raise_for_status()
    soup = BeautifulSoup(response.content, "html.parser")

    return get_single_page_products(soup)


def get_dynamic_products(page_url: str) -> list[Product]:
    """Function runs browser and clicks 'more' button to get full html of the
        page and calls the function that creates a list of [Products] from a
        single page"""

    logging.info(f"Dynamic parsing: {page_url}")

    driver = get_driver()
    wait = WebDriverWait(driver, 15)

    driver.get(page_url)

    # We are waiting for appearing at least one card
    wait.until(
        ec.presence_of_all_elements_located(
            (By.CSS_SELECTOR, "div.col-md-4")
        )
    )

    while True:
        products_before = driver.find_elements(By.CSS_SELECTOR, "div.col-md-4")
        count_before = len(products_before)

        try:
            more_button = driver.find_element(
                By.CSS_SELECTOR,
                "a.btn.btn-primary.ecomerce-items-scroll-more"
            )

            driver.execute_script("arguments[0].click();", more_button)

            # Waiting for increase in quantity of the cards
            wait.until(
                lambda d: len(
                    d.find_elements(By.CSS_SELECTOR, "div.col-md-4")
                ) > count_before
            )

        except (NoSuchElementException, TimeoutException):
            break

    soup = BeautifulSoup(driver.page_source, "html.parser")
    products = get_single_page_products(soup)

    logging.info(f"Dynamic found {len(products)} products")

    return products


def get_any_page_products(page_url: str) -> list[Product]:
    """Function checks if the page has pagination or 'more' button
    and runs a corresponding function to get all products - static
    or dynamic"""

    dynamic_pages = {LAPTOP_URL, TABLETS_URL, TOUCH_URL}

    if page_url in dynamic_pages:
        return get_dynamic_products(page_url)
    else:
        return get_static_products(page_url)


def write_products_to_csv(products: list[Product], file_name: str) -> None:
    """Function to write products to a CSV file."""

    with open(file_name, "w") as f:
        writer = csv.writer(f)
        writer.writerow(PRODUCT_FIELDS)
        writer.writerows([astuple(product) for product in products])


def get_all_products() -> None:
    """Function calls get_any_page_products() and write_products_to_csv()
    every single url of the website from the list ALL_URL. It sets driver
    in context manager to use it during the work of the dynamic function"""

    with webdriver.Chrome() as driver:
        set_driver(driver)

        for url, file_name in ALL_URL.items():
            all_products_from_url = get_any_page_products(url)
            write_products_to_csv(all_products_from_url, file_name)


if __name__ == "__main__":
    get_all_products()
