import csv
import dataclasses
from pathlib import Path
from urllib.parse import urljoin
from enum import StrEnum
from selenium import webdriver
from selenium.common import (
    TimeoutException,
    ElementNotInteractableException,
    ElementClickInterceptedException
)
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC  # noqa
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from tqdm import tqdm

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")
BASE_DIR = Path(__file__).resolve().parent.parent


class DriverManager:
    _driver: WebDriver | None = None

    @classmethod
    def get_driver(cls) -> WebDriver:
        if cls._driver is None:
            options = webdriver.ChromeOptions()
            options.add_argument("--headless=new")
            cls._driver = webdriver.Chrome(options=options)
        return cls._driver


class UrlEnum(StrEnum):
    HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")
    COMPUTER_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/computers")
    LAPTOP_URL = urljoin(
        BASE_URL, "test-sites/e-commerce/more/computers/laptops"
    )
    TABLET_URL = urljoin(
        BASE_URL, "test-sites/e-commerce/more/computers/tablets"
    )
    PHONE_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/phones")
    TOUCH_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/phones/touch")

    @classmethod
    def list(cls) -> list["UrlEnum"]:
        return [url for url in cls]


@dataclasses.dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int

    @classmethod
    def headers(cls) -> list[str]:
        return [field.name for field in dataclasses.fields(cls)]

    def to_row(self) -> list[str]:
        return [
            self.title or "",
            self.description or "",
            float(self.price) if self.price is not None else 0.0,
            int(self.rating) if self.rating is not None else 0,
            int(self.num_of_reviews) if self.num_of_reviews is not None else 0,
        ]


def _handle_accept_cookies_message() -> None:
    driver = DriverManager.get_driver()
    sec = 3
    try:
        cookie_accept_message = WebDriverWait(driver, sec).until(
            EC.presence_of_element_located((By.CLASS_NAME, "acceptCookies"))
        )
        cookie_accept_message.click()

    except (TimeoutException, ElementNotInteractableException):
        pass


def _handle_more_button() -> None:
    driver = DriverManager.get_driver()
    sec = 3
    try:
        while True:
            more_button = WebDriverWait(driver, sec).until(
                EC.element_to_be_clickable(
                    (By.CLASS_NAME, "ecomerce-items-scroll-more")
                )
            )
            more_button.click()
            WebDriverWait(driver, 1)

    except (
            TimeoutException,
            ElementNotInteractableException,
            ElementClickInterceptedException
    ):
        pass


def parse_product(product: WebElement) -> Product:
    price = float(
        product.find_element(By.CLASS_NAME, "price").text.replace("$", "", 1)
    )
    title = (
        product.find_element(By.CSS_SELECTOR, "a.title")
        .get_attribute("title")
    )
    description = product.find_element(By.CLASS_NAME, "description").text
    num_of_reviews = int(
        product.find_element(By.CSS_SELECTOR, ".review-count span").text
    )
    rating = len(product.find_elements(By.CLASS_NAME, "ws-icon-star"))
    return Product(
        title=title,
        description=description,
        rating=rating,
        price=price,
        num_of_reviews=num_of_reviews
    )


def get_specific_products(product_url: UrlEnum) -> list[Product]:
    driver = DriverManager.get_driver()
    driver.get(product_url)
    _handle_accept_cookies_message()
    _handle_more_button()
    products = driver.find_elements(By.CLASS_NAME, "product-wrapper")

    return [
        parse_product(product)
        for product in products
    ]


def write_to_file(output_csv_path: str, products: list[Product]) -> None:
    with open(f"{output_csv_path}.csv", "w", newline="") as file_out:
        writer = csv.writer(file_out)
        writer.writerow(Product.headers())
        for product in products:
            writer.writerow(product.to_row())


product_name_map = {
    UrlEnum.HOME_URL: "home",
    UrlEnum.PHONE_URL: "phones",
    UrlEnum.TABLET_URL: "tablets",
    UrlEnum.COMPUTER_URL: "computers",
    UrlEnum.TOUCH_URL: "touch",
    UrlEnum.LAPTOP_URL: "laptops"
}


def get_all_products() -> None:
    for product_url in tqdm(UrlEnum.list(), desc="scraping products"):
        specific_products = get_specific_products(product_url)
        filename = str(BASE_DIR / product_name_map.get(product_url))
        write_to_file(filename, specific_products)


if __name__ == "__main__":
    get_all_products()
