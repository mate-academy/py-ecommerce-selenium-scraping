import csv
import time
from dataclasses import dataclass, fields
from urllib.parse import urljoin

from bs4 import BeautifulSoup, Tag
from selenium import webdriver
from selenium.common import (
    ElementClickInterceptedException,
    NoSuchElementException
)
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from tqdm import tqdm
from webdriver_manager.chrome import ChromeDriverManager

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")
URLS = {
    "home": urljoin(BASE_URL, "test-sites/e-commerce/more"),
    "computers": urljoin(BASE_URL, "test-sites/e-commerce/more/computers"),
    "laptops": urljoin(BASE_URL, "test-sites/e-commerce/more/computers/laptops"),  # noqa: E501
    "tablets": urljoin(BASE_URL, "test-sites/e-commerce/more/computers/tablets"),  # noqa: E501
    "phones": urljoin(BASE_URL, "test-sites/e-commerce/more/phones"),
    "touch": urljoin(BASE_URL, "test-sites/e-commerce/more/phones/touch"),
}


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


def create_product(tag_product: Tag) -> Product:
    return Product(
        title=tag_product.select_one(".title")["title"],
        description=tag_product.select_one(
            ".description"
        ).text.replace("\xa0", " ").strip(),
        price=float(tag_product.select_one(
            ".price"
        ).text.replace("$", "").replace(",", "").strip()),
        rating=len(tag_product.select(".ratings .ws-icon-star")),
        num_of_reviews=int(
            tag_product.select_one(".review-count").text.split()[0]
        )

    )


def get_products_from_page(page_url: str, driver: WebDriver) -> list[Product]:

    try:
        driver.get(page_url)
        cookies = driver.find_elements(By.CLASS_NAME, "acceptCookies")
        if cookies:
            cookies[0].click()
    except (NoSuchElementException, ElementClickInterceptedException) as e:
        print(f"An error occurred while handling cookies: {e}")

    try:
        buttons = driver.find_elements(
            By.CLASS_NAME,
            "ecomerce-items-scroll-more"
        )
        while buttons and buttons[0].is_displayed():
            buttons[0].click()
            time.sleep(0.2)
    except (NoSuchElementException, ElementClickInterceptedException) as e:
        print(f"An error occurred while clicking load more buttons: {e}")

    soup = BeautifulSoup(driver.page_source, "html.parser")
    products = soup.select(".thumbnail")

    return [create_product(tag_product) for tag_product in products]


def save_data(file_path: str, products: list[Product]) -> None:
    with open(file_path, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow([field.name for field in fields(Product)])
        for product in products:
            writer.writerow([
                product.title,
                product.description,
                product.price,
                product.rating,
                product.num_of_reviews
            ])


def get_all_products() -> None:
    option = webdriver.ChromeOptions()
    option.add_argument("--headless")
    service = Service(ChromeDriverManager().install())
    with webdriver.Chrome(service=service, options=option) as driver:
        for name, url in tqdm(URLS.items()):
            products = get_products_from_page(url, driver)
            file_name = f"{name}.csv"
            save_data(file_name, products)


if __name__ == "__main__":
    get_all_products()
