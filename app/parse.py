import csv
import time
from dataclasses import dataclass
from urllib.parse import urljoin
from selenium import webdriver
from selenium.common import TimeoutException, NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.ie.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from tqdm import tqdm

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


PAGES = {
    "home": HOME_URL,
    "computers": urljoin(HOME_URL, "computers"),
    "laptops": urljoin(HOME_URL, "computers/laptops"),
    "tablets": urljoin(HOME_URL, "computers/tablets"),
    "phones": urljoin(HOME_URL, "phones"),
    "touch": urljoin(HOME_URL, "phones/touch"),
}


def driver_setup(headless: bool = True) -> WebDriver:
    options = webdriver.FirefoxOptions()
    if headless:
        options.add_argument("--headless")
    return webdriver.Firefox(options=options)


def cookies(driver: WebDriver) -> None:
    try:
        WebDriverWait(driver, 10).until(
            ec.presence_of_element_located((By.CLASS_NAME, "cookie-btn"))
        ).click()
    except TimeoutException:
        pass


def get_prod(item: WebElement) -> Product:
    title = item.find_element(By.CLASS_NAME, "title").text
    description = item.find_element(By.CLASS_NAME, "description").text
    price = float(
        item.find_element(By.CLASS_NAME, "price").text.replace("$", "")
    )
    rating = len(item.find_elements(By.CLASS_NAME, "glyphicon-star"))
    reviews = item.find_element(By.CLASS_NAME, "ratings").text
    num_of_reviews = int(reviews.split()[0])

    return Product(title, description, price, rating, num_of_reviews)


def get_page(driver: WebDriver) -> list[Product]:
    products = []
    while True:
        WebDriverWait(driver, 10).until(
            ec.presence_of_element_located((By.CLASS_NAME, "card"))
        )
        items = driver.find_elements(By.CLASS_NAME, "card")

        for item in items:
            try:
                product = get_prod(item)
                if product:
                    products.append(product)
            except NoSuchElementException:
                continue

        try:
            more = driver.find_element(By.CLASS_NAME, "show-more-btn")
            if not more.is_displayed():
                break
            more.click()
        except NoSuchElementException:
            break

    return products


def save_to_file(products: list[Product], filename: str) -> None:
    fields = ["title", "description", "price", "rating", "num_of_reviews"]

    with open(f"{filename}.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()

        for product in products:
            writer.writerow(
                {
                    "title": str(product.title),
                    "description": str(product.description),
                    "price": float(product.price),
                    "rating": int(product.rating),
                    "num_of_reviews": int(product.num_of_reviews),
                }
            )


def get_all_products() -> None:
    driver = driver_setup(headless=True)
    try:
        for name, url in tqdm(PAGES.items(), desc="Pages"):
            driver.get(url)
            cookies(driver)
            products = get_page(driver)
            save_to_file(products, name)
    finally:
        driver.quit()


if __name__ == "__main__":
    get_all_products()
