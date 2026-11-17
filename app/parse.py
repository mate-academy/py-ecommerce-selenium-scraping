import csv
from dataclasses import dataclass, fields, astuple
from urllib.parse import urljoin

from selenium import webdriver
from selenium.common.exceptions import (
    NoSuchElementException,
    TimeoutException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait
from tqdm import tqdm

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")

PAGES = {
    "home": "",
    "computers": "computers",
    "laptops": "computers/laptops",
    "tablets": "computers/tablets",
    "phones": "phones",
    "touch": "phones/touch",
}

PRODUCT_SELECTOR = ".product-wrapper"
MORE_BUTTON_SELECTOR = ".ecomerce-items-scroll-more"


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


PRODUCT_FIELDS = [field.name for field in fields(Product)]


def decline_cookies(driver: WebDriver) -> None:
    try:
        WebDriverWait(driver, 5).until(
            expected_conditions.element_to_be_clickable(
                (By.CSS_SELECTOR, "[data-tracking='cookieDeclined']")
            )
        ).click()
    except TimeoutException:
        pass  # banner did not appear


def load_all_products(driver: WebDriver) -> None:
    """Click the 'more' button until all products are loaded."""
    while True:
        try:
            more_button = driver.find_element(
                By.CSS_SELECTOR, MORE_BUTTON_SELECTOR
            )
        except NoSuchElementException:
            return  # page without a "more" button

        if not more_button.is_displayed():
            return  # everything is loaded

        count_before = len(
            driver.find_elements(By.CSS_SELECTOR, PRODUCT_SELECTOR)
        )
        driver.execute_script("arguments[0].click();", more_button)

        try:
            WebDriverWait(driver, 5).until(
                lambda d: len(
                    d.find_elements(By.CSS_SELECTOR, PRODUCT_SELECTOR)
                ) > count_before
            )
        except TimeoutException:
            return  # nothing new appeared


def parse_single_product(product: WebElement) -> Product:
    title = product.find_element(
        By.CSS_SELECTOR, "a.title"
    ).get_attribute("title")
    description = product.find_element(By.CSS_SELECTOR, ".description").text
    price = float(
        product.find_element(By.CSS_SELECTOR, ".price")
        .text.replace("$", "")
    )
    rating = len(product.find_elements(By.CSS_SELECTOR, ".ws-icon-star"))
    num_of_reviews = int(
        product.find_element(By.CSS_SELECTOR, ".review-count span")
        .get_attribute("textContent")
    )

    return Product(
        title=title,
        description=description,
        price=price,
        rating=rating,
        num_of_reviews=num_of_reviews,
    )


def scrape_page(driver: WebDriver, url: str) -> list[Product]:
    driver.get(url)
    load_all_products(driver)
    elements = driver.find_elements(By.CSS_SELECTOR, PRODUCT_SELECTOR)
    return [parse_single_product(element) for element in elements]


def write_to_csv(products: list[Product], output_csv_path: str) -> None:
    with open(output_csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(PRODUCT_FIELDS)
        writer.writerows(astuple(product) for product in products)


def get_all_products() -> None:

    with webdriver.Chrome() as driver:
        driver.get(HOME_URL)
        decline_cookies(driver)

        for name, path in tqdm(PAGES.items(), desc="Scraping pages"):
            products = scrape_page(driver, urljoin(HOME_URL, path))
            write_to_csv(products, f"{name}.csv")


if __name__ == "__main__":
    get_all_products()
