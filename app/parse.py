from dataclasses import dataclass
from selenium import webdriver
from selenium.common import NoSuchElementException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from urllib.parse import urljoin
import pandas as pd
from webdriver_manager.chrome import ChromeDriverManager

BASE_URL = "https://webscraper.io/test-sites/e-commerce/more/"


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


def get_driver() -> WebDriver:
    options = Options()
    options.headless = True
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    return driver


def scrape_page(driver: WebDriver, url: str) -> list[Product]:
    driver.get(url)
    products = []

    while True:
        try:
            more_button = driver.find_element(By.CLASS_NAME, "btn.btn-primary")
            driver.execute_script("arguments[0].click();", more_button)

            if "display: none" in more_button.get_attribute("style"):
                break
        except NoSuchElementException:
            break

    product_elements = driver.find_elements(By.CLASS_NAME, "thumbnail")
    for product_element in product_elements:
        title = product_element.find_element(
            By.CLASS_NAME, "title").get_attribute("title")
        description = product_element.find_element(
            By.CLASS_NAME, "description").text
        price = float(product_element.find_element(
            By.CLASS_NAME, "price").text.replace("$", ""))
        rating = len(product_element.find_elements(
            By.CLASS_NAME, "ws-icon-star"))
        num_of_reviews = int(product_element.find_element(
            By.CLASS_NAME, "ratings").text.split()[0])

        product = Product(title, description, price, rating, num_of_reviews)
        products.append(product)

    return products


def save_products_to_csv(products: list[Product], filename: str) -> None:
    product_data = {
        "title": [p.title for p in products],
        "description": [p.description for p in products],
        "price": [p.price for p in products],
        "rating": [p.rating for p in products],
        "num_of_reviews": [p.num_of_reviews for p in products],
    }

    df = pd.DataFrame(product_data)
    df.to_csv(filename, index=False)


def get_all_products() -> None:
    driver = get_driver()
    to_scrape = {
        "home.csv": "",
        "computers.csv": "computers",
        "laptops.csv": "computers/laptops",
        "tablets.csv": "computers/tablets",
        "phones.csv": "computers/tablets",
        "touch.csv": "phones/touch"
    }
    try:
        for filename, link in to_scrape.items():
            products = scrape_page(driver, urljoin(BASE_URL, link))
            save_products_to_csv(products, filename)
    finally:
        driver.quit()


if __name__ == "__main__":
    get_all_products()
