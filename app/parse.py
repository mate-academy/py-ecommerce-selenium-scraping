import csv
import logging
from dataclasses import dataclass, fields, astuple
from urllib.parse import urljoin
from typing import List, Dict

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common import (
    NoSuchElementException,
    ElementNotInteractableException,
    ElementClickInterceptedException,
    TimeoutException,
    WebDriverException
)
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

BASE_URL = "https://webscraper.io/"


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int
    additional_info: dict


PRODUCT_FIELDS = [field.name for field in fields(Product)]


def product_hdd_block_prices(driver: WebDriver, product_soup: BeautifulSoup) -> dict[str, float]:
    """Get HDD block prices from the product detail page."""
    detail_url = urljoin(BASE_URL, product_soup.select_one(".title")["href"])
    driver.get(detail_url)

    prices = {}
    try:
        swatches = driver.find_element(By.CLASS_NAME, "swatches")
        if swatches:
            buttons = swatches.find_elements(By.TAG_NAME, "button")
            for button in buttons:
                if not button.get_property("disabled"):
                    button.click()
                    prices[button.get_property("value")] = float(
                        driver.find_element(By.CLASS_NAME, "price").text.replace("$", "")
                    )
    except NoSuchElementException:
        return prices

    return prices


def parse_single_product(driver: WebDriver, product_soup: BeautifulSoup) -> Product:
    """Parse a single product from the soup object."""
    hdd_prices = product_hdd_block_prices(driver, product_soup)
    return Product(
        title=product_soup.select_one(".title")["title"],
        description=product_soup.select_one(".description").text,
        price=float(product_soup.select_one(".price").text.replace("$", "")),
        rating=len(product_soup.select(".ratings span.ws-icon.ws-icon-star")),
        num_of_reviews=int(product_soup.select_one(".review-count").text.split()[0]),
        additional_info={"hdd_prices": hdd_prices}
    )


def get_page_products(url: str, driver: WebDriver, paginate: bool = False) -> List[Product]:
    """Get products from a single page, with optional pagination."""
    logging.info(f"Start scraping products from {url}")
    driver.get(url)

    if paginate:
        while True:
            try:
                more_button = driver.find_element(By.CLASS_NAME, "ecommerce-items-scroll-more")
                more_button.click()
            except NoSuchElementException:
                logging.info(f"No more 'load more' button found, pagination complete.")
                break
            except ElementClickInterceptedException:
                logging.warning(f"Click on 'load more' intercepted, retrying...")
            except TimeoutException:
                logging.error(f"Page load timeout reached while waiting for 'load more' button.")
            except WebDriverException as e:
                logging.error(f"Webdriver error occurred: {e}")
                break
            except Exception as e:
                logging.error(f"Unexpected error during pagination: {e}")
                break

    page_soup = BeautifulSoup(driver.page_source, "html.parser")
    product_soups = page_soup.select(".thumbnail")

    return [parse_single_product(driver, product_soup) for product_soup in product_soups]


def write_products_to_csv(products: List[Product], filename: str) -> None:
    """Write products to a CSV file."""
    with open(filename, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(PRODUCT_FIELDS)
        for product in products:
            writer.writerow(astuple(product))


def get_all_products() -> None:
    """Scrape all products from predefined pages and save them to CSV files."""
    with webdriver.Chrome() as driver:
        pages_info = {
            "home": {"path": "test-sites/e-commerce/more/"},
            "computers": {"path": "test-sites/e-commerce/more/computers"},
            "laptops": {"path": "test-sites/e-commerce/more/computers/laptops"},
            "tablets": {"path": "test-sites/e-commerce/more/computers/tablets"},
            "phones": {"path": "test-sites/e-commerce/more/phones"},
            "touch": {"path": "test-sites/e-commerce/more/phones/touch"},
        }

        for name, info in pages_info.items():
            url = urljoin(BASE_URL, info["path"])
            all_products = []
            driver.get(url)

            while True:
                products = driver.find_elements(By.CLASS_NAME, "product-item")
                for product in products:
                    all_products.append(product.text)

                try:
                    next_button = driver.find_element(By.CSS_SELECTOR, "a.page-link.next")
                    next_button.click()
                except NoSuchElementException:
                    break

            with open(f"{name}.csv", "w", newline="", encoding="utf-8") as file:
                writer = csv.writer(file)
                writer.writerow(["Product Details"])
                for product in all_products:
                    writer.writerow([product])

    if __name__ == "__main__":
        get_all_products()
