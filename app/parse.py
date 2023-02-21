import csv
import time
from dataclasses import dataclass, fields, astuple
from urllib.parse import urljoin

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")
COMPUTER_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/computers")
LAPTOPS_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/computers/laptops")
TABLETS_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/computers/tablets")
PHONE_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/phones")
TOUCH_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/phones/touch")

urls = {
    "home.csv": HOME_URL,
    "computers.csv": COMPUTER_URL,
    "laptops.csv": LAPTOPS_URL,
    "tablets.csv": TABLETS_URL,
    "phones.csv": PHONE_URL,
    "touch.csv": TOUCH_URL,
}


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


class Driver:
    _driver: WebDriver | None = None

    @classmethod
    def get_driver(cls) -> WebDriver:
        return cls._driver

    @classmethod
    def set_driver(cls, new_driver: webdriver) -> None:
        cls._driver = new_driver


def parse_single_product(product: WebElement) -> Product:
    return Product(
        title=product.find_element(
            By.CLASS_NAME, "title"
        ).get_attribute("title"),
        description=product.find_element(By.CLASS_NAME, "description").text,
        price=float(
            product.find_element(By.CLASS_NAME, "price").text.replace("$", "")
        ),
        rating=int(len(product.find_elements(By.CLASS_NAME, "glyphicon"))),
        num_of_reviews=int(
            product.find_element(By.CLASS_NAME, "ratings").
            find_element(By.TAG_NAME, "p").text.split()[0]
        ),
    )


def get_page(url: str) -> None:
    driver = Driver.get_driver()
    driver.get(url)
    if len(driver.find_elements(By.CLASS_NAME, "acceptCookies")):
        driver.find_element(By.CLASS_NAME, "acceptCookies").click()

    if len(driver.find_elements(By.CLASS_NAME, "ecomerce-items-scroll-more")):
        button = driver.find_element(
            By.CLASS_NAME, "ecomerce-items-scroll-more"
        )
        while not button.get_property("style"):
            button.click()
            time.sleep(0.1)
        products = driver.find_elements(By.CLASS_NAME, "thumbnail")
    else:
        products = driver.find_elements(By.CLASS_NAME, "thumbnail")

    return [parse_single_product(product) for product in products]


def write_products_to_csv(name: str, products: [Product]) -> None:
    product_fields = [field.name for field in fields(Product)]
    with open(name, "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(product_fields)
        writer.writerows([astuple(product) for product in products])


def get_all_products() -> None:
    with webdriver.Chrome() as new_driver:
        Driver.set_driver(new_driver)
        for name, url in urls.items():
            write_products_to_csv(name, get_page(url))


if __name__ == "__main__":
    start = time.perf_counter()
    get_all_products()
    print(f"Elapsed: {time.perf_counter() - start}")
