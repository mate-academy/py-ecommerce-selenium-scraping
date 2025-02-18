import csv
from dataclasses import dataclass, fields
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common import (
    ElementNotInteractableException,
    ElementClickInterceptedException,
)
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")
CATEGORIES = {
    "home": HOME_URL,
    "computers": urljoin(HOME_URL, "computers"),
    "laptops": urljoin(HOME_URL, "computers/laptops"),
    "tablets": urljoin(HOME_URL, "computers/tablets"),
    "phones": urljoin(HOME_URL, "phones"),
    "touch": urljoin(HOME_URL, "phones/touch"),
}
options = Options()
options.add_argument("--headless")


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


PRODUCT_FIELDS = [field.name for field in fields(Product)]


def get_pagination_page(url) -> list[str]:
    driver = webdriver.Chrome(options=options)

    driver.get(url)

    accept_button = driver.find_element(By.CLASS_NAME, "acceptCookies")
    if accept_button is not None:
        accept_button.click()
    try:
        while True:
            more_button = driver.find_element(By.CLASS_NAME, "btn")
            if more_button:
                more_button.click()
            else:
                break
    except (ElementNotInteractableException, ElementClickInterceptedException):
        print("Parsing page ended")
    page_source = []
    all_page_links = driver.find_elements(By.CSS_SELECTOR, "a.title")
    for link in all_page_links:
        link = link.get_attribute("href")
        page_source.append(link)
    driver.close()

    return page_source


def get_products_from_page(url):
    driver = webdriver.Chrome(options=options)

    driver.get(url)
    product = Product(
        title=driver.find_element(By.CLASS_NAME, "title").text,
        description=driver.find_element(By.CLASS_NAME, "description").text,
        price=float(
            driver.find_element(By.CLASS_NAME, "price").text.replace("$", "").strip()
        ),
        rating=len(driver.find_elements(By.CLASS_NAME, "ws-icon-star")),
        num_of_reviews=int(
            driver.find_element(By.CLASS_NAME, "review-count").text.split()[0]
        ),
    )
    driver.close()
    return product


def get_all_products() -> dict[str, list[Product]]:
    detail_url = {}
    for category, url in CATEGORIES.items():
        text = requests.get(url).content
        product_soup = BeautifulSoup(text, "html.parser")
        items_on_page = product_soup.select(".card-body")
        if len(items_on_page) != 3:
            detail_url[category] = get_pagination_page(url)
        else:
            detail_url[category] = []
        detail_url[category] += [
            urljoin(BASE_URL, a["href"]) for a in product_soup.select(".title")
        ]
    products = {}
    for items_cat, items_url in detail_url.items():

        products[items_cat] = []
        for items in items_url:
            products[items_cat].append(get_products_from_page(items))
    return products


def put_data_in_file() -> None:
    products = get_all_products()
    for category_name, category_item in products.items():
        file_name = f"{category_name}.csv"
        with open(file_name, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(PRODUCT_FIELDS)
            for product in category_item:
                writer.writerow(
                    [
                        product.title,
                        product.description,
                        product.price,
                        product.rating,
                        product.num_of_reviews,
                    ]
                )


if __name__ == "__main__":
    put_data_in_file()
