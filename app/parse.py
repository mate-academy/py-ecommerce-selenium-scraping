import csv
import time
from dataclasses import dataclass, asdict
from typing import List, Optional
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options


BASE_URL = "https://webscraper.io/"
URL_PATHS = {
    "home": "test-sites/e-commerce/more/",
    "computers": "test-sites/e-commerce/more/computers/",
    "laptops": "test-sites/e-commerce/more/computers/laptops/",
    "tablets": "test-sites/e-commerce/more/computers/tablets/",
    "phones": "test-sites/e-commerce/more/phones/",
    "touch": "test-sites/e-commerce/more/phones/touch/"
}

URLS = {name: urljoin(BASE_URL, path) for name, path in URL_PATHS.items()}


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


def parse_product_details(soup: BeautifulSoup) -> Optional[Product]:
    try:
        title = soup.select_one(".title")["title"]
        description = soup.select_one(".description").text
        price = float(soup.select_one(".price").text.replace("$", ""))
        rating = int(soup.select_one("p[data-rating]")["data-rating"])
        num_of_reviews = int(soup.select_one(".ratings > p.float-end")
                             .text.split()[0])
        return Product(title, description, price, rating, num_of_reviews)
    except (AttributeError, TypeError, ValueError):
        return None


def fetch_products_from_static_page(url: str) -> List[Product]:
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    return [parse_product_details(product) for product in
            soup.select(".thumbnail") if parse_product_details(product)]


def fetch_products_with_load_more(url: str) -> List[Product]:
    options = Options()
    options.headless = True
    service = ChromeService(executable_path="path/to/chromedriver")
    driver = webdriver.Chrome(service=service, options=options)
    driver.get(url)
    collected_products = []

    try:
        while True:
            page_source = driver.page_source
            soup = BeautifulSoup(page_source, "html.parser")
            collected_products.extend(
                [parse_product_details(product) for product in soup.select(".thumbnail") if parse_product_details(product)]
            )
            load_more_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable(
                    By.CLASS_NAME,
                    "ecomerce-items-scroll-more"
                )
            )
            driver.execute_script("arguments[0].click();", load_more_button)
            time.sleep(2)
    except Exception:
        pass
    finally:
        driver.quit()

    return collected_products


def detect_pagination(url: str) -> bool:
    options = Options()
    options.headless = True
    service = ChromeService(executable_path="path/to/chromedriver")
    driver = webdriver.Chrome(service=service, options=options)
    driver.get(url)

    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "ecomerce-items-scroll-more"))
        )
        return True
    except Exception:
        return False
    finally:
        driver.quit()


def save_products_to_csv(products: List[Product], filename: str) -> None:
    with open(filename, mode="w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(
            csvfile,
            fieldnames=Product.__annotations__.keys()
        )
        writer.writeheader()
        for product in products:
            writer.writerow(asdict(product))


def get_all_products() -> None:
    category_config = {
        "home": (URLS["home"], "home.csv"),
        "computers": (URLS["computers"], "computers.csv"),
        "laptops": (URLS["laptops"], "laptops.csv"),
        "tablets": (URLS["tablets"], "tablets.csv"),
        "phones": (URLS["phones"], "phones.csv"),
        "touch": (URLS["touch"], "touch.csv"),
    }

    for category, (url, filename) in category_config.items():
        if detect_pagination(url):
            products = fetch_products_with_load_more(url)
        else:
            products = fetch_products_from_static_page(url)
        save_products_to_csv(products, filename)


if __name__ == "__main__":
    get_all_products()
