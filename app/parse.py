import csv
from dataclasses import dataclass, astuple, fields
from time import sleep
from urllib.parse import urljoin

from selenium.common import NoSuchElementException
from selenium.webdriver.chrome import webdriver
from selenium.webdriver.firefox.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")
COMPUTERS_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/computers")
LAPTOPS_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/computers/laptops")
TABLETS_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/computers/tablets")
PHONES_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/phones")
TOUCH_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/phones/touch")

URLS_AND_FILES = {
    HOME_URL: "home.csv",
    COMPUTERS_URL: "computers.csv",
    LAPTOPS_URL: "laptops.csv",
    TABLETS_URL: "tablets.csv",
    PHONES_URL: "phones.csv",
    TOUCH_URL: "touch.csv"
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
        title=(
            product.find_element(By.CLASS_NAME, "title").get_attribute("title")
        ),
        description=product.find_element(By.CLASS_NAME, "description").text,
        price=float(
            product.find_element(By.CLASS_NAME, "price")
            .text.replace("$", "")
        ),
        rating=len(product.find_elements(By.CLASS_NAME, "glyphicon-star")),
        num_of_reviews=int(
            product.find_element(By.CLASS_NAME, "ratings")
            .find_element(By.TAG_NAME, "p")
            .text.split()[0]
        )
    )


def get_all_url_products(page_url: str) -> list[WebElement]:
    driver = get_driver()
    driver.get(page_url)
    sleep(2)

    try:
        driver.find_element(By.ID, "closeCookieBanner").click()
    except NoSuchElementException:
        pass
    sleep(2)
    while True:
        try:
            driver.find_element(By.LINK_TEXT, "More").click()
        except NoSuchElementException:
            break

    products = driver.find_elements(By.CLASS_NAME, "thumbnail")
    return products


def write_products_to_csv(path: str, products: [Product]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(PRODUCT_FIELDS)
        writer.writerows([astuple(product) for product in products])


def get_all_products() -> None:
    with webdriver.Firefox() as new_driver:
        set_driver(new_driver)
        for url, path in URLS_AND_FILES.items():
            products = get_all_url_products(url)
            all_products = []
            for product in products:
                all_products.append(parse_single_product(product))
            write_products_to_csv(path, all_products)


if __name__ == "__main__":
    get_all_products()
