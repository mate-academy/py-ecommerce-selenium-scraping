from typing import List, Dict
from dataclasses import dataclass, asdict
from selenium import webdriver
from selenium.common.exceptions import (
    NoSuchElementException,
    WebDriverException,
)
from selenium.webdriver.common.by import By
from urllib.parse import urljoin
import csv


BASE_URL = "https://webscraper.io/"
PRODUCT_FIELDS = ["title", "description", "price", "rating", "num_of_reviews"]
PRODUCT_CSV = {
    "home.csv": "test-sites/e-commerce/more/",
    "computers.csv": "test-sites/e-commerce/more/computers/",
    "laptops.csv": "test-sites/e-commerce/more/computers/laptops",
    "tablets.csv": "test-sites/e-commerce/more/computers/tablets",
    "phones.csv": "test-sites/e-commerce/more/phones/",
    "touch.csv": "test-sites/e-commerce/more/phones/touch",
}


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


def cookies(driver: webdriver) -> None:
    try:
        driver.find_element(By.CLASS_NAME, "acceptCookies").click()
    except NoSuchElementException:
        pass


def click_more_products_button(driver: webdriver) -> None:
    try:
        more_button = driver.find_element(By.LINK_TEXT, "More")
        while True:
            try:
                more_button.click()
            except WebDriverException:
                break
    except NoSuchElementException:
        pass


def get_detail_info(driver: webdriver) -> List[Dict[str, str]]:
    products = driver.find_elements(By.CLASS_NAME, "thumbnail")
    all_info = []
    for product in products:
        info = {
            "title": product.find_element(
                By.CSS_SELECTOR, "a.title"
            ).get_attribute("title"),
            "price": float(
                product.find_element(By.CLASS_NAME, "price").text.replace(
                    "$", ""
                )
            ),
            "description": product.find_element(
                By.CLASS_NAME, "description"
            ).text,
            "rating": len(
                product.find_elements(By.CLASS_NAME, "glyphicon-star")
            ),
            "num_of_reviews": int(
                product.find_element(
                    By.CSS_SELECTOR, ".ratings > .pull-right"
                ).text.split(" ")[0]
            ),
        }
        all_info.append(info)
    return all_info


def get_products(driver: webdriver, url: str) -> List[Product]:
    driver.get(urljoin(BASE_URL, url))
    cookies(driver)
    click_more_products_button(driver)
    return [
        Product(**product_info) for product_info in get_detail_info(driver)
    ]


def get_all_products() -> None:
    with webdriver.Chrome() as driver:
        all_products = {}
        for csv_path, url in PRODUCT_CSV.items():
            all_products[csv_path] = get_products(driver, url)
        write_csv(all_products)


def write_csv(products: Dict[str, List[Product]]) -> None:
    for csv_path, product_list in products.items():
        with open(csv_path, "w", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=PRODUCT_FIELDS)
            writer.writeheader()
            writer.writerows(asdict(product) for product in product_list)


if __name__ == "__main__":
    get_all_products()
