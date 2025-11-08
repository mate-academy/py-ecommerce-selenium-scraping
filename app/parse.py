import csv
import time
from dataclasses import dataclass, fields, astuple
from typing import List, Literal
from urllib.parse import urljoin
from selenium import webdriver
from selenium.common import (
    StaleElementReferenceException,
    NoSuchElementException,
    TimeoutException
)
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")
driver: WebDriver | None = None
PRODUCT_FIELDS = fields(Product)


def get_driver() -> WebDriver:
    global driver
    if not driver:
        options = Options()
        options.add_argument("--headless=new")
        driver = webdriver.Chrome(options=options)
        return driver
    return driver


def get_page_product(element: WebElement) -> Product:
    review_count = element.find_element(By.CLASS_NAME, "review-count")

    return Product(
        title=element
        .find_element(By.CLASS_NAME, "title")
        .get_attribute("title"),
        description=element
        .find_element(By.CLASS_NAME, "description")
        .text,
        price=float(
            element
            .find_element(By.CLASS_NAME, "price")
            .text.replace("$", "")
        ),
        rating=int(
            len(element
                .find_elements(By.CLASS_NAME, "ws-icon-star")
                )
        ),
        num_of_reviews=int(
            review_count
            .find_element(By.TAG_NAME, "span").text
        )
    )


def get_products_page() -> List[Product]:
    scraped_products = WebDriverWait(driver, 5).until(
        ec.presence_of_all_elements_located((By.CLASS_NAME, "card-body"))
    )
    products = []

    for product in scraped_products:
        products.append(get_page_product(product))

    return products


def is_visible(driver: WebDriver, by: Literal[str], value: str) -> bool:
    try:
        element = driver.find_element(by, value)
        return element.is_displayed()
    except (NoSuchElementException, StaleElementReferenceException):
        return False


def get_all_products() -> None:
    tasks = [
        (
            "https://webscraper.io/test-sites/e-commerce/more",
            "home.csv"
        ),
        (
            "https://webscraper.io/test-sites/e-commerce/more/computers",
            "computers.csv"
        ),
        (
            "https://webscraper.io/test-sites/"
            "e-commerce/more/computers/laptops",
            "laptops.csv"
        ),
        (
            "https://webscraper.io/test-sites/"
            "e-commerce/more/computers/tablets",
            "tablets.csv"
        ),
        (
            "https://webscraper.io/test-sites/e-commerce/more/phones",
            "phones.csv"
        ),
        (
            "https://webscraper.io/test-sites/e-commerce/more/phones/touch",
            "touch.csv"
        )
    ]
    try:
        for task in tasks:
            write_csv_file(get_all(task[0]), task[1])
    finally:
        driver = get_driver()
        driver.close()


def get_all(url: str) -> List[Product]:
    driver = get_driver()
    driver.get(url)
    wait = WebDriverWait(driver, 5)
    is_button_visible = is_visible(
        driver,
        By.CLASS_NAME,
        "ecomerce-items-scroll-more"
    )

    cookies = driver.find_elements(By.CLASS_NAME, "acceptCookies")
    if cookies:
        wait.until(ec.element_to_be_clickable(
            (By.CLASS_NAME, "acceptCookies"))).click()

    while is_button_visible:
        try:
            wait.until(ec.element_to_be_clickable(
                (By.CLASS_NAME, "ecomerce-items-scroll-more"))).click()
            time.sleep(0.5)
        except TimeoutException:
            break
        is_button_visible = is_visible(
            driver,
            By.CLASS_NAME,
            "ecomerce-items-scroll-more"
        )
    return get_products_page()


def write_csv_file(products: List[Product], output_csv_path: str) -> None:
    with open(output_csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([field.name for field in PRODUCT_FIELDS])
        writer.writerows([astuple(product) for product in products])


if __name__ == "__main__":
    get_all_products()
