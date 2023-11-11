import csv
import time
from dataclasses import dataclass, fields, astuple
from urllib.parse import urljoin

from selenium import webdriver
from selenium.common import (
    NoSuchElementException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")
URLS = {
    "home": HOME_URL,
    "computers": urljoin(HOME_URL, "computers"),
    "laptops": urljoin(HOME_URL, "computers/laptops"),
    "tablets": urljoin(HOME_URL, "computers/tablets"),
    "phones": urljoin(HOME_URL, "phones"),
    "touch": urljoin(HOME_URL, "phones/touch"),
}


class Driver:
    def __init__(self) -> None:
        op = webdriver.ChromeOptions()
        op.add_argument("headless")
        self.driver = webdriver.Chrome(options=op)

    def get_driver(self) -> WebDriver:
        return self.driver


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


PRODUCT_FIELDS = [field.name for field in fields(Product)]


def get_single_product(product: WebElement) -> Product:
    return Product(
        title=product.find_element(By.CSS_SELECTOR, "h4 > a").get_attribute(
            "title"
        ),
        description=product.find_element(By.CLASS_NAME, "description").text,
        price=float(
            product.find_element(By.CLASS_NAME, "price").text.replace("$", "")
        ),
        rating=len(product.find_elements(By.CLASS_NAME, "ws-icon-star")),
        num_of_reviews=int(
            product.find_element(By.CLASS_NAME, "review-count").text.split()[0]
        ),
    )


def get_all_products(products: [WebElement]) -> [Product]:
    return [get_single_product(product) for product in products]


def write_products_to_csv_file(
        products: [Product], output_csv_path: str
) -> None:
    with open(output_csv_path, "w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(PRODUCT_FIELDS)
        writer.writerows([astuple(product) for product in products])


def click_more_button(driver) -> None:
    while True:
        try:
            more_button = driver.find_element(
                By.CLASS_NAME, "ecomerce-items-scroll-more"
            )
        except NoSuchElementException:
            break
        else:
            if not more_button.is_displayed():
                break
            more_button.click()
            time.sleep(0.1)


def accept_cookies(driver) -> None:
    cookie_button = driver.find_element(By.CLASS_NAME, "acceptCookies")
    cookie_button.click()


def main() -> None:
    driver = Driver().get_driver()
    driver.get(HOME_URL)
    accept_cookies(driver)

    for file_name, url in URLS.items():
        print("=====" * 10)
        print(f"Scrapping page: {url}")
        driver.get(url)
        click_more_button(driver)
        products = get_all_products(
            driver.find_elements(By.CLASS_NAME, "product-wrapper")
        )
        print(f"Found {len(products)} items")
        write_products_to_csv_file(products, f"{file_name}.csv")
        print(f"Created csv file with name {file_name}.csv")
        print("=====" * 10)


if __name__ == "__main__":
    main()
