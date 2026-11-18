import csv
from dataclasses import astuple, dataclass, fields
from urllib.parse import urljoin
from selenium import webdriver
from selenium.common.exceptions import (
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

PRODUCT_SELECTOR = ".thumbnail"
MORE_BUTTON_SELECTOR = ".ecomerce-items-scroll-more"
COOKIES_BUTTON_SELECTOR = ".acceptCookies"


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


PRODUCT_FIELDS = [field.name for field in fields(Product)]


def create_driver() -> WebDriver:
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--window-size=1920,1080")
    return webdriver.Chrome(options=options)


def accept_cookies(driver: WebDriver) -> None:
    try:
        button = WebDriverWait(driver, 3).until(
            ec.element_to_be_clickable(
                (By.CSS_SELECTOR, COOKIES_BUTTON_SELECTOR)
            )
        )
        button.click()
    except TimeoutException:
        pass


def load_all_products(driver: WebDriver) -> None:
    while True:
        try:
            more_button = driver.find_element(
                By.CSS_SELECTOR, MORE_BUTTON_SELECTOR
            )
        except NoSuchElementException:
            return

        if not more_button.is_displayed():
            return

        loaded = len(driver.find_elements(By.CSS_SELECTOR, PRODUCT_SELECTOR))
        driver.execute_script("arguments[0].click();", more_button)
        WebDriverWait(driver, 10).until(
            lambda d: len(d.find_elements(By.CSS_SELECTOR, PRODUCT_SELECTOR))
            > loaded
        )


def parse_rating(product: WebElement) -> int:
    try:
        rating = product.find_element(
            By.CSS_SELECTOR, ".ratings p[data-rating]"
        ).get_attribute("data-rating")
        return int(rating)
    except NoSuchElementException:
        return len(
            product.find_elements(By.CSS_SELECTOR, ".ratings .ws-icon-star")
        )


def parse_single_product(product: WebElement) -> Product:
    return Product(
        title=product.find_element(
            By.CSS_SELECTOR, ".title"
        ).get_attribute("title"),
        description=product.find_element(
            By.CSS_SELECTOR, ".description"
        ).text,
        price=float(
            product.find_element(By.CSS_SELECTOR, ".price")
            .text.replace("$", "")
        ),
        rating=parse_rating(product),
        num_of_reviews=int(
            product.find_element(By.CSS_SELECTOR, ".review-count")
            .text.split()[0]
        ),
    )


def parse_page(driver: WebDriver, url: str) -> list[Product]:
    driver.get(url)
    accept_cookies(driver)
    load_all_products(driver)
    products = driver.find_elements(By.CSS_SELECTOR, PRODUCT_SELECTOR)
    return [parse_single_product(product) for product in products]


def write_products_to_csv(products: list[Product], file_name: str) -> None:
    with open(file_name, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(PRODUCT_FIELDS)
        writer.writerows(astuple(product) for product in products)


def get_all_products() -> None:
    with create_driver() as driver:
        progress = tqdm(PAGES.items(), desc="Scraping pages", unit="page")
        for page_name, url in progress:
            progress.set_postfix(page=page_name)
            products = parse_page(driver, url)
            write_products_to_csv(products, f"{page_name}.csv")


if __name__ == "__main__":
    get_all_products()
