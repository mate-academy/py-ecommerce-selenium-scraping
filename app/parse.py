
import csv
import time
from dataclasses import astuple, dataclass, fields
from urllib.parse import urljoin

from selenium import webdriver
from selenium.common.exceptions import (
    ElementClickInterceptedException,
    NoSuchElementException,
    TimeoutException,
)
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait
from tqdm import tqdm

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")

PAGES = {
    "home": HOME_URL,
    "computers": urljoin(HOME_URL, "computers"),
    "laptops": urljoin(HOME_URL, "computers/laptops"),
    "tablets": urljoin(HOME_URL, "computers/tablets"),
    "phones": urljoin(HOME_URL, "phones"),
    "touch": urljoin(HOME_URL, "phones/touch"),
}


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


PRODUCT_FIELDS = [field.name for field in fields(Product)]


def get_driver() -> WebDriver:
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--window-size=1920,1080")
    return webdriver.Chrome(options=options)


def accept_cookies(driver: WebDriver) -> None:
    try:
        WebDriverWait(driver, 5).until(
            ec.element_to_be_clickable((By.CLASS_NAME, "acceptCookies"))
        ).click()
    except (NoSuchElementException, TimeoutException):
        pass


def click_show_more(driver: WebDriver) -> None:
    while True:
        try:
            more_button = driver.find_element(
                By.CLASS_NAME, "ecomerce-items-scroll-more"
            )
            if not more_button.is_displayed():
                break
            try:
                more_button.click()
            except ElementClickInterceptedException:
                driver.execute_script(
                    "arguments[0].click();", more_button
                )
            time.sleep(0.5)
        except NoSuchElementException:
            break


def parse_rating(product: WebElement) -> int:
    rating_elements = product.find_elements(
        By.CSS_SELECTOR, "p[data-rating]"
    )
    if rating_elements:
        return int(rating_elements[0].get_attribute("data-rating"))
    return len(product.find_elements(By.CLASS_NAME, "ws-icon-star"))


def parse_single_product(product: WebElement) -> Product:
    title = product.find_element(
        By.CLASS_NAME, "title"
    ).get_attribute("title")
    description = product.find_element(
        By.CLASS_NAME, "description"
    ).text
    price = float(
        product.find_element(By.CLASS_NAME, "price")
        .text.replace("$", "")
    )
    num_of_reviews = int(
        product.find_element(By.CLASS_NAME, "review-count")
        .text.split()[0]
    )

    return Product(
        title=title,
        description=description,
        price=price,
        rating=parse_rating(product),
        num_of_reviews=num_of_reviews,
    )


def get_single_page_products(driver: WebDriver, url: str) -> list[Product]:
    driver.get(url)
    accept_cookies(driver)
    click_show_more(driver)

    products = driver.find_elements(By.CLASS_NAME, "thumbnail")
    return [
        parse_single_product(product)
        for product in products
        if product.find_elements(By.CLASS_NAME, "title")
    ]


def write_products_to_csv(products: list[Product], filename: str) -> None:
    with open(filename, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(PRODUCT_FIELDS)
        writer.writerows([astuple(product) for product in products])


def get_all_products() -> None:
    with get_driver() as driver:
        for page_name, url in tqdm(PAGES.items(), desc="Scraping pages"):
            products = get_single_page_products(driver, url)
            write_products_to_csv(products, f"{page_name}.csv")


if __name__ == "__main__":
    get_all_products()
