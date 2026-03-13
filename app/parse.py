import csv
from dataclasses import dataclass, fields
from selenium.webdriver.support import expected_conditions as EC
from urllib.parse import urljoin
from dataclasses import asdict
from selenium import webdriver
from selenium.common import TimeoutException, NoSuchElementException
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By

from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.expected_conditions import presence_of_all_elements_located
from selenium.webdriver.support.wait import WebDriverWait


BASE_URL = "https://webscraper.io/test-sites/e-commerce/more/"
COMPUTERS_URL = urljoin(BASE_URL, "computers")
PHONES_URL = urljoin(BASE_URL, "phones")
LAPTOPS_URL = urljoin(BASE_URL, "computers/laptops")
TABLETS_URL = urljoin(BASE_URL, "computers/tablets")
TOUCH_URL = urljoin(BASE_URL, "phones/touch")

_driver: WebDriver | None = None

def get_driver() -> WebDriver:
    return _driver

def set_driver(new_driver: WebDriver) -> None:
    global _driver
    _driver = new_driver

def accept_cookies(driver: WebDriver) -> None:
    try:
        cookie_btn = WebDriverWait(driver, 3).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, ".accept-cookies"))
        )
        cookie_btn.click()
    except TimeoutException:
        pass

@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int

FIELD_NAMES = [field.name for field in fields(Product)]


def parse_single_product(product: WebElement) -> Product:
    title = product.find_element(By.CLASS_NAME, "title").text.strip()
    description = product.find_element(By.CLASS_NAME, "description").text.strip()
    price = float(product.find_element(By.CSS_SELECTOR, "h4.price span[itemprop='price']").text.replace("$", ""))
    rating = 0
    try:
        rating_el = product.find_element(By.CLASS_NAME, "ratings")
        rating = int(rating_el.get_attribute("data-rating"))
    except NoSuchElementException:
        pass
    num_of_reviews = int(product.find_element(By.CLASS_NAME, "review-count").text.split()[0])

    return Product(
        title=title,
        description=description,
        price=price,
        rating=rating,
        num_of_reviews=num_of_reviews,
    )

def parse_page(absolute_url) -> list[Product]:
    driver = get_driver()
    driver.get(absolute_url)
    accept_cookies(driver)
    WebDriverWait(driver, 10).until(
        presence_of_all_elements_located((By.CLASS_NAME, "product-wrapper")))
    products = []
    prev = 0
    while True:
        elements = driver.find_elements(By.CLASS_NAME, "product-wrapper")
        for el in elements[len(products):]:
            products.append(parse_single_product(el))
        try:
            more_btn = WebDriverWait(driver, 2).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, ".btn.btn-default.btn-block")))
        except TimeoutException:
            break
        prev = len(elements)
        more_btn.click()
        WebDriverWait(driver, 5).until(
            lambda d: len(d.find_elements(By.CLASS_NAME, "product-wrapper")) > prev)
    return products

def write_csv(filename: str, products: list[Product]) -> None:
    with open(filename, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELD_NAMES)
        writer.writeheader()
        for product in products:
            writer.writerow(asdict(product))

def get_all_products() -> None:
    pages = [
        (BASE_URL, "home.csv"),
        (COMPUTERS_URL, "computers.csv"),
        (PHONES_URL, "phones.csv"),
        (LAPTOPS_URL, "laptops.csv"),
        (TABLETS_URL, "tablets.csv"),
        (TOUCH_URL, "touch.csv"),
    ]
    try:
        for url, filename in pages:
            products = parse_page(url)
            write_csv(filename, products)
    finally:
        pass

if __name__ == "__main__":
    driver = webdriver.Chrome()
    set_driver(driver)
    try:
        get_all_products()
    finally:
        driver.quit()

