import csv
import time
from dataclasses import dataclass, fields, astuple
from urllib.parse import urljoin

from selenium import webdriver
from selenium.common import NoSuchElementException, TimeoutException
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


PRODUCT_FIELDS = [field.name for field in fields(Product)]


def parse_single_product(product: WebElement) -> Product:
    title = product.find_element(
        By.CSS_SELECTOR, ".title").get_attribute("title")
    description = product.find_element(
        By.CSS_SELECTOR, ".description").text
    price = float(product.find_element(
        By.CSS_SELECTOR, ".price").text.replace("$", ""))
    rating = len(product.find_elements(
        By.CSS_SELECTOR, ".ratings span.ws-icon-star"))
    num_of_reviews = int(product.find_element(
        By.CSS_SELECTOR, ".review-count").text.split()[0])

    return Product(
        title=title,
        description=description,
        price=price,
        rating=rating,
        num_of_reviews=num_of_reviews
    )


def get_products(url: str) -> list[Product]:
    with webdriver.Chrome() as driver:
        driver.get(url)

        while True:
            try:
                more_button_selector = (
                    "a.btn.btn-lg.btn-block.btn-primary.ecomerce-items-scroll-more"
                )
                button = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, more_button_selector))
                )

                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", button)

                driver.execute_script("arguments[0].click();", button)
                time.sleep(0.5)

            except (NoSuchElementException, TimeoutException):
                print("No more products to load.")
                break

        products = driver.find_elements(By.CLASS_NAME, "card-body")
        return [parse_single_product(product) for product in products]


def write_products_csv(products: list[Product], file_name: str) -> None:
    with open(file_name, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(PRODUCT_FIELDS)
        writer.writerows([astuple(product) for product in products])


def get_all_products() -> None:
    write_products_csv(
        get_products(HOME_URL), "home.csv")
    write_products_csv(
        get_products(urljoin(HOME_URL, "computers")), "computers.csv")
    write_products_csv(
        get_products(urljoin(HOME_URL, "computers/laptops")), "laptops.csv")
    write_products_csv(
        get_products(urljoin(HOME_URL, "computers/tablets")), "tablets.csv")
    write_products_csv(
        get_products(urljoin(HOME_URL, "phones")), "phones.csv")
    write_products_csv(
        get_products(urljoin(HOME_URL, "phones/touch")), "touch.csv")


if __name__ == "__main__":
    get_all_products()
