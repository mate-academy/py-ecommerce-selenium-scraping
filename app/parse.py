import csv
import time
from bs4 import BeautifulSoup
from dataclasses import dataclass
from urllib.parse import urljoin
from tqdm import tqdm
from typing import Optional, List
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import ElementNotInteractableException

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


def get_all_products() -> None:
    pages = [
        {"url": "", "name": "home"},
        {"url": "computers", "name": "computers"},
        {"url": "phones", "name": "phones"},
        {"url": "computers/laptops", "name": "laptops", "additional_url":
            "test-sites/e-commerce/more/computers/laptops"},
        {"url": "computers/tablets", "name": "tablets", "additional_url":
            "test-sites/e-commerce/more/computers/tablets"},
        {"url": "phones/touch", "name": "touch", "additional_url":
            "test-sites/e-commerce/more/phones/touch"}
    ]
    options = Options()
    service = Service("path/to/chromedriver")
    driver = webdriver.Chrome(service=service, options=options)
    driver.get(HOME_URL)
    time.sleep(2)
    accept_cookies_button = driver.find_elements(
        By.CSS_SELECTOR, ".acceptCookies"
    )
    if accept_cookies_button:
        accept_cookies_button[0].click()
        time.sleep(2)
    for page in pages:
        dynamic_url = urljoin(
            BASE_URL, page["additional_url"]
        ) if page.get("additional_url") else None
        product_list = scrape_page(driver, page["name"], dynamic_url)
        scrape_with_progress(product_list, page["name"])
        save_to_csv(product_list, page["name"])
    driver.quit()


def scrape_page(
    driver: webdriver.Chrome, page_name: str,
        dynamic_url: Optional[str] = None
) -> List[Product]:
    if dynamic_url:
        driver.get(dynamic_url)
        time.sleep(2)
        while True:
            try:
                more_button = WebDriverWait(driver, 20).until(
                    ec.element_to_be_clickable((By.CSS_SELECTOR,
                        "a.ecomerce-items-scroll-more"))
                )
                driver.execute_script("arguments[0].scrollIntoView(true);",
                    more_button)
                time.sleep(1)
                more_button.click()
            except ElementNotInteractableException:
                break
    soup = BeautifulSoup(driver.page_source, "html.parser")
    products = soup.select(".thumbnail")
    product_list = scrape_one_products_page(products)
    return product_list


def scrape_one_products_page(products: List[BeautifulSoup]) -> List[Product]:
    product_list = []
    for product in products:
        title_element = product.select_one(".title")
        title = (
            title_element["title"] if "title"
                in title_element.attrs else title_element.text.strip()
        )
        description = (
            product.select_one(".description").text.strip().replace("\xa0", " ")
        )
        price = float(product.select_one(".price").text.strip().replace("$", ""))
        rating = len(product.select(".glyphicon-star"))
        num_of_reviews_element = product.select_one(".ratings .pull-right")
        num_of_reviews_text = num_of_reviews_element.text.strip()
        num_of_reviews = int(num_of_reviews_text.split()[0]) if num_of_reviews_text else 0
        scraped_product = Product(title, description, price, rating, num_of_reviews)
        product_list.append(scraped_product)
    return product_list


def scrape_with_progress(products: List[Product], page_name: str) -> None:
    with tqdm(total=len(products), desc=f"Scraping {page_name}") as pbar:
        for product in products:
            pbar.update(1)


def save_to_csv(products: List[Product], page_name: str) -> None:
    with open(f"{page_name}.csv", "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow([
            "title", "description", "price", "rating", "num_of_reviews"
        ])
        for product in products:
            writer.writerow(
                [product.title, product.description, product.price,
                 product.rating, product.num_of_reviews]
            )


if __name__ == "__main__":
    get_all_products()
