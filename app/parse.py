from dataclasses import dataclass, fields, astuple
from urllib.parse import urljoin
from selenium import webdriver
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.common.exceptions import (
    TimeoutException,
    ElementNotInteractableException
)
from bs4 import BeautifulSoup
import csv

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")
PHONES_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/phones/")
TOUCH_URL = urljoin(PHONES_URL, "touch")
COMPUTERS_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/computers/")
TABLETS_URL = urljoin(COMPUTERS_URL, "tablets")
LAPTOPS_URL = urljoin(COMPUTERS_URL, "laptops")

HOME_FILE = "home.csv"
PHONES_FILE = "phones.csv"
TOUCH_FILE = "touch.csv"
COMPUTERS_FILE = "computers.csv"
TABLETS_FILE = "tablets.csv"
LAPTOPS_FILE = "laptops.csv"


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


HEADER = [field.name for field in fields(Product)]

file_url_mapper = {
    HOME_FILE: HOME_URL,
    PHONES_FILE: PHONES_URL,
    TOUCH_FILE: TOUCH_URL,
    COMPUTERS_FILE: COMPUTERS_URL,
    TABLETS_FILE: TABLETS_URL,
    LAPTOPS_FILE: LAPTOPS_URL
}


def get_file_url_mapper() -> dict:
    return file_url_mapper


def get_chrome_driver() -> WebDriver:
    return webdriver.Chrome()


def accept_cookie(driver: WebDriver) -> None:
    try:
        WebDriverWait(driver, 2).until(
            ec.visibility_of_element_located(
                (By.CLASS_NAME, "acceptCookies")
            )
        )
        WebDriverWait(driver, 2).until(
            ec.element_to_be_clickable(
                (By.CLASS_NAME, "acceptCookies")
            )
        ).click()
        print("COOKIE button clicked")
    except (TimeoutException, ElementNotInteractableException):
        pass


def load_page(driver: WebDriver) -> None:
    try:
        WebDriverWait(driver, 2).until(
            ec.visibility_of_element_located(
                (
                    By.CLASS_NAME,
                    "ecomerce-items-scroll-more"
                )
            )
        )
        while True:
            driver.execute_script(
                "arguments[0].click();",
                WebDriverWait(driver, 2).until(
                    ec.element_to_be_clickable(
                        (
                            By.CLASS_NAME,
                            "ecomerce-items-scroll-more"
                        )
                    )
                )
            )
    except (TimeoutException, ElementNotInteractableException):
        return


def write_products_to_csv(file_path: str, products: list[Product]):
    with open(file_path, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)

        writer.writerow(HEADER)
        writer.writerows([astuple(product) for product in products])


def get_single_product(driver: WebDriver) -> Product:
    return Product(
        title=driver.find_element(By.CLASS_NAME, "title").get_attribute("title"),
        description=driver.find_element(By.CLASS_NAME, "description").text,
        price=float(
            driver.find_element(
                By.CLASS_NAME, "price"
            ).text.replace("$", "")
        ),
        rating=len(
            driver.find_elements(
                By.CLASS_NAME,
                "ws-icon-star"
            )
        ),
        num_of_reviews=int(
            driver.find_element(
                By.CLASS_NAME,
                "review-count"
            ).text.split()[0]
        )
    )


def get_product_cards(url: str, driver: WebDriver = get_chrome_driver()) -> list[WebDriver]:
    driver.get(url)

    accept_cookie(driver)
    load_page(driver)

    return driver.find_elements(By.CLASS_NAME, "product-wrapper")


def get_all_products(
        mapper: dict = get_file_url_mapper(),
) -> None:
    for file, url in mapper.items():
        products_cards = get_product_cards(url)

        print(f"Collecting products from {url}")

        write_products_to_csv(
            file,
            [get_single_product(product_card)
             for product_card in products_cards]
        )



if __name__ == "__main__":
    get_all_products()
