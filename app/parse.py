import time
import csv
from dataclasses import dataclass, astuple, fields
from urllib.parse import urljoin

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")
COMPUTERS_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/computers")
LAPTOPS_URL = urljoin(
    BASE_URL,
    "test-sites/e-commerce/more/computers/laptops"
)
TABLETS_URL = urljoin(
    BASE_URL,
    "test-sites/e-commerce/more/computers/tablets"
)
PHONES_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/phones")
TOUCH_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/phones/touch")

URLS = {
    HOME_URL: "home.csv",
    COMPUTERS_URL: "computers.csv",
    LAPTOPS_URL: "laptops.csv",
    TABLETS_URL: "tablets.csv",
    PHONES_URL: "phones.csv",
    TOUCH_URL: "touch.csv",
}


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


PRODUCT_FIELDS = [field.name for field in fields(Product)]


class Driver:
    _driver: WebDriver | None = None

    @classmethod
    def get_driver(cls) -> WebDriver:
        return cls._driver

    @classmethod
    def set_driver(cls, new_driver: WebDriver) -> None:
        cls._driver = new_driver


def parse_page(url: str) -> list[WebElement]:
    driver = Driver.get_driver()
    driver.get(url)

    time.sleep(1.5)

    if len(driver.find_elements(By.CLASS_NAME, "acceptCookies")):
        cookies = driver.find_element(By.CLASS_NAME, "acceptCookies")
        cookies.click()

    if len(driver.find_elements(By.CLASS_NAME, "ecomerce-items-scroll-more")):
        more_button = driver.find_element(
            By.CLASS_NAME, "ecomerce-items-scroll-more"
        )
        while more_button.is_displayed():
            more_button.click()
            time.sleep(0.1)

    products = driver.find_elements(By.CLASS_NAME, "thumbnail")
    return products


def get_single_product(product: WebElement) -> Product:
    return Product(
        title=product.find_element(
            By.CLASS_NAME, "title").get_attribute("title"),
        description=product.find_element(By.CLASS_NAME, "description").text,
        price=float(product.find_element(
            By.CLASS_NAME, "price").text.replace("$", "")),
        rating=len(product.find_elements(By.CLASS_NAME, "glyphicon-star")),
        num_of_reviews=int(product.find_element(
            By.CLASS_NAME, "ratings"
        ).find_element(
            By.TAG_NAME, "p"
        ).text.split(" ")[0]),
    )


def get_all_products() -> None:
    with webdriver.Chrome() as new_driver:
        new_driver.set_window_position(-20, 0)
        Driver.set_driver(new_driver)
        for url, file_name in URLS.items():
            products = parse_page(url)
            result = [get_single_product(product) for product in products]
            write_products_to_csv(file_name, result)


def write_products_to_csv(file_name: str, products: [Product]) -> None:
    with open(file_name, "w") as file:
        writer = csv.writer(file)
        writer.writerow(PRODUCT_FIELDS)
        writer.writerows([astuple(product) for product in products])


if __name__ == "__main__":
    start = time.perf_counter()
    get_all_products()
    end = time.perf_counter()

    print("Elapsed:", end - start)
