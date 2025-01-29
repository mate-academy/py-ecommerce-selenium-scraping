import csv
from dataclasses import dataclass, fields, astuple
from urllib.parse import urljoin


from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import (
    NoSuchElementException,
    ElementNotInteractableException,
    ElementClickInterceptedException,
)


BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")
URLS_FOR_PARSING = {
    "home": HOME_URL,
    "computers": urljoin(HOME_URL, "computers"),
    "laptops": urljoin(HOME_URL, "computers/laptops"),
    "tablets": urljoin(HOME_URL, "computers/tablets"),
    "phones": urljoin(HOME_URL, "phones"),
    "touch": urljoin(HOME_URL, "phones/touch"),
}

_driver: WebDriver | None = None


def get_driver() -> WebDriver:
    return _driver


def set_driver(new_driver: WebDriver) -> None:
    global _driver
    _driver = new_driver


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


PRODUCT_FIELDS = [field.name for field in fields(Product)]


def parse_single_product(product: WebElement) -> Product:
    return Product(
        title=product.find_element(By.CLASS_NAME, "title").get_attribute(
            "title"
        ),
        description=product.find_element(By.CLASS_NAME, "description").text,
        price=float(
            product.find_element(By.CLASS_NAME, "price").text.replace("$", "")
        ),
        rating=len(product.find_elements(By.CLASS_NAME, "ws-icon-star")),
        num_of_reviews=int(
            product.find_element(By.CLASS_NAME, "ratings").text.split()[0]
        ),
    )


def get_all_products_from_section(url: str) -> list[Product]:
    driver = get_driver()
    driver.get(url)

    if cookies := driver.find_elements(By.CLASS_NAME, "acceptCookies"):
        cookies[0].click()

    while True:
        try:
            driver.find_element(
                By.CLASS_NAME, "ecomerce-items-scroll-more"
            ).click()
        except (
            NoSuchElementException,
            ElementNotInteractableException,
            ElementClickInterceptedException,
        ):
            break

    products = driver.find_elements(By.CLASS_NAME, "product-wrapper")
    return [parse_single_product(product) for product in products]


def write_section_to_csv(csv_name: str, products: list[Product]) -> None:
    with open(csv_name + ".csv", "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(PRODUCT_FIELDS)
        writer.writerows([astuple(product) for product in products])


def get_all_products() -> None:

    with webdriver.Chrome() as driver:
        set_driver(driver)
        for csv_name, url in URLS_FOR_PARSING.items():
            write_section_to_csv(csv_name, get_all_products_from_section(url))


if __name__ == "__main__":
    get_all_products()