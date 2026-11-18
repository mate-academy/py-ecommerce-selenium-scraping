import csv

from dataclasses import dataclass, asdict, fields
from pathlib import Path
from typing import Any
from urllib.parse import urljoin
from selenium import webdriver
from selenium.common import TimeoutException, StaleElementReferenceException
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec


BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")
COMPUTERS_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/computers")
LAPTOPS_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/computers/laptops")
TABLETS_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/computers/tablets")
PHONES_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/phones")
TOUCHES_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/phones/touch")

MORE_BTN = "a.ecomerce-items-scroll-more"
ITEM = ".product-wrapper.card-body"

PAGES_WITH_PAGINATION = {
    "laptops": LAPTOPS_URL,
    "tablets": TABLETS_URL,
    "touch": TOUCHES_URL,
    "phones": PHONES_URL,
    "computers": COMPUTERS_URL,
    "home": HOME_URL,
}


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


def parse_products(driver: WebDriver) -> list[Product]:
    result = []
    for product in driver.find_elements(By.CSS_SELECTOR, ITEM):
        title = product.find_element(
            By.CLASS_NAME,
            "title").get_attribute("title")
        description = product.find_element(
            By.CLASS_NAME,
            "description").text
        price = float(product.find_element(
            By.CLASS_NAME,
            "price").text.replace("$", "").replace(",", ""))
        num_of_reviews = int(product.find_element(
            By.CSS_SELECTOR,
            ".review-count.float-end").text.split()[0])

        rating_elems = product.find_elements(
            By.CSS_SELECTOR,
            "p[data-rating]")
        rating = int(rating_elems[0].get_attribute("data-rating")) \
            if rating_elems else 5

        product_item = Product(
            title=title,
            description=description,
            price=price,
            rating=rating,
            num_of_reviews=num_of_reviews,
        )
        result.append(product_item)
        print(product_item)
    return result


def load_all_products(driver: WebDriver) -> None:
    wait = WebDriverWait(driver, 10)
    while True:
        count_before = len(driver.find_elements(By.CSS_SELECTOR, ITEM))
        try:
            btn = wait.until(
                ec.presence_of_element_located((By.CSS_SELECTOR, MORE_BTN))
            )
            if not btn.is_displayed():
                break
            driver.execute_script(
                "arguments[0].scrollIntoView({block: 'center'});", btn
            )
            driver.execute_script("arguments[0].click();", btn)
        except (TimeoutException, StaleElementReferenceException):
            break

        try:
            wait.until(
                lambda d: len(d.find_elements(
                    By.CSS_SELECTOR,
                    ITEM
                )) > count_before
            )
        except TimeoutException:
            break


def get_page_with_pagination(url: str) -> list[Any]:
    driver = webdriver.Chrome()
    try:
        driver.get(url)
        load_all_products(driver)
        return parse_products(driver)
    finally:
        driver.quit()


def write_products_to_csv(products: list[Product], path: Path) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, fieldnames=[fld.name for fld in fields(Product)]
        )
        writer.writeheader()
        writer.writerows(asdict(p) for p in products)


def get_all_products() -> None:
    driver = webdriver.Chrome()
    try:
        for name, url in PAGES_WITH_PAGINATION.items():
            products = get_page_with_pagination(url)
            write_products_to_csv(products, f"{name}.csv")
            print(f"{name}: {len(products)} товаров -> output/{name}.csv")
    finally:
        driver.quit()


if __name__ == "__main__":
    get_all_products()
