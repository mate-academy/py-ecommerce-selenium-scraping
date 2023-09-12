import csv
from dataclasses import dataclass, fields, astuple
from urllib.parse import urljoin

from selenium import webdriver
from selenium.common import (
    TimeoutException,
    NoSuchElementException,
    ElementClickInterceptedException,
    ElementNotInteractableException,
)
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.ui import WebDriverWait
from tqdm import tqdm

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


PRODUCTS_FIELDS = [field.name for field in fields(Product)]


def parse_single_product(driver: WebDriver) -> Product:
    product = Product(
        title=driver.find_element(
            By.CSS_SELECTOR, "a[title]"
        ).get_attribute("title"),
        description=driver.find_element(By.CLASS_NAME, "description").text,
        price=float(
            driver.find_element(By.CLASS_NAME, "price").text.replace("$", "")
        ),
        rating=5,
        num_of_reviews=int(driver.find_element(
            By.CSS_SELECTOR, ".ratings > .float-end"
        ).text.split(" ")[0])
    )
    try:
        rating = driver.find_element(
            By.CSS_SELECTOR, "p[data-rating]"
        ).get_attribute("data-rating")
        product.rating = int(rating)
    except NoSuchElementException:
        product.rating = 5

    return product


class Driver:
    def __init__(self) -> None:
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument("--headless")
        self.driver = webdriver.Chrome(options=chrome_options)

    def cookies_button(self) -> None:
        while True:
            try:
                accept_cookies_button = (
                    self.driver.find_element(By.CLASS_NAME, "acceptCookies")
                )
                accept_cookies_button.click()
            except (
                    NoSuchElementException,
                    ElementClickInterceptedException,
                    ElementNotInteractableException,
                    TimeoutException
            ):
                break

    def get_more_button(self) -> None:
        while True:
            try:
                more_button = WebDriverWait(self.driver, 5).until(
                    expected_conditions.element_to_be_clickable(
                        (By.CLASS_NAME, "ecomerce-items-scroll-more")
                    )
                )
                more_button.click()
            except (
                    ElementClickInterceptedException,
                    ElementNotInteractableException,
                    TimeoutException
            ):
                break

    def get_page_of_products(self) -> list[Product]:
        self.cookies_button()
        self.get_more_button()

        products = self.driver.find_elements(By.CLASS_NAME, "card-body")
        products_list = []
        for product in tqdm(products, desc="Processing"):
            products_list.append(parse_single_product(product))
        return products_list

    def get_products(self, url) -> list[Product]:
        self.driver.get(url)
        products_list = self.get_page_of_products()

        return products_list

    def close_driver(self):
        self.driver.close()


def write_products_to_csv(products: [Product], output_csv_path: str) -> None:
    with open(output_csv_path, "w") as file:
        writer = csv.writer(file)
        writer.writerow(PRODUCTS_FIELDS)
        writer.writerows([astuple(product) for product in products])


def get_all_products() -> None:
    driver = Driver()

    url_computers = urljoin(HOME_URL, "computers/")
    url_laptops = urljoin(HOME_URL, "computers/laptops")
    url_tablets = urljoin(HOME_URL, "computers/tablets")
    url_phones = urljoin(HOME_URL, "phones")
    url_touch = urljoin(HOME_URL, "phones/touch")

    urls = [
        HOME_URL,
        url_computers,
        url_laptops,
        url_tablets,
        url_phones,
        url_touch
    ]

    csv_files = [
        "home.csv",
        "computers.csv",
        "laptops.csv",
        "tablets.csv",
        "phones.csv",
        "touch.csv"
    ]

    for url, file in zip(urls, csv_files):
        products = driver.get_products(url)
        write_products_to_csv(products, file)

    driver.close_driver()


if __name__ == "__main__":
    get_all_products()
