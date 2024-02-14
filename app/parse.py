import csv
from dataclasses import dataclass, fields
from time import sleep
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import StaleElementReferenceException

BASE_URL = "https://webscraper.io/"

WEBSITE_URLS = {
    # "home": urljoin(BASE_URL, "test-sites/e-commerce/more/"),
    # "computers": urljoin(BASE_URL, "test-sites/e-commerce/more/computers/"),
    # "laptops": urljoin(BASE_URL, "test-sites/e-commerce/more/computers/laptops/"),
    "tablets": urljoin(BASE_URL, "test-sites/e-commerce/more/computers/tablets/"),
    # "phones": urljoin(BASE_URL, "test-sites/e-commerce/more/phones/"),
    # "touch": urljoin(BASE_URL, "test-sites/e-commerce/more/phones/touch/")
}


class DriverManager:
    def __init__(self):
        self._driver = None

    def get_driver(self) -> WebDriver:
        return self._driver

    def set_driver(self, new_driver: WebDriver) -> None:
        self._driver = new_driver


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
        title=product.find_element(By.CLASS_NAME, "title").get_property("title"),
        description=product.find_element(By.CLASS_NAME, "description").text,
        price=float(product.find_element(By.CLASS_NAME, "price").text.replace("$", "")),
        rating=len(product.find_elements(By.CLASS_NAME, "ws-icon-star")),
        num_of_reviews=int(
            product.find_element(By.CLASS_NAME, "review-count").text.split()[0]
        ),
    )


def get_single_page_products(page: WebDriver) -> list[Product]:
    products = page.find_elements(By.CLASS_NAME, "thumbnail")

    return [parse_single_product(product) for product in products]


# def click_all_more_buttons_and_accept_cookies(page_url: str, driver: DriverManager()) -> WebDriver:
#     driver = driver.get_driver()
#     driver.get(page_url)
#
#     try:
#         cookies_button = driver.find_elements(
#             By.CLASS_NAME, "acceptCookies"
#         )
#         if cookies_button:
#             cookies_button[0].click()
#         more_button = driver.find_elements(By.CLASS_NAME, "ecomerce-items-scroll-more")
#         if more_button:
#             more_button = more_button[0]
#             while more_button.is_displayed():
#                 more_button.click()
#                 sleep(2)
#
#     finally:
#         return driver


def write_products_to_csv(output_csv_path: str, products: [Product]) -> None:
    with open(output_csv_path, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=PRODUCT_FIELDS)

        writer.writeheader()
        for product in products:
            writer.writerow(
                {
                    "title": product.title,
                    "description": product.description,
                    "price": product.price,
                    "rating": product.rating,
                    "num_of_reviews": product.num_of_reviews
                }
            )


def get_all_products() -> None:
    # options = Options()
    # options.add_argument("--headless=new")

    with webdriver.Chrome() as new_driver:
        driver = DriverManager()
        driver.set_driver(new_driver)
        driver = driver.get_driver()
        for name, url in WEBSITE_URLS.items():
            driver.get(url)
            sleep(2)

            cookies_button = driver.find_element(
                By.CLASS_NAME, "acceptCookies"
            )
            if cookies_button:
                cookies_button.click()

            more_button = driver.find_element(By.CLASS_NAME, "ecomerce-items-scroll-more")

            if more_button:
                try:
                    while more_button.is_displayed():
                        more_button.click()
                        sleep(2)
                except StaleElementReferenceException as e:
                    print(e)
            products = get_single_page_products(driver)
            write_products_to_csv(f"{name}.csv", products)


if __name__ == "__main__":
    get_all_products()
