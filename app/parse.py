import csv
from dataclasses import dataclass, fields, astuple
from urllib.parse import urljoin
from unicodedata import normalize

from bs4 import BeautifulSoup, Tag
from selenium import webdriver
from selenium.common import (
    NoSuchElementException, ElementNotInteractableException
)
from selenium.webdriver import Chrome
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec

HOME_URL = "https://webscraper.io/test-sites/e-commerce/more/"

PAGES = [
    {"name": "home", "url": HOME_URL},
    {"name": "computers", "url": urljoin(HOME_URL, "computers")},
    {"name": "laptops", "url": urljoin(HOME_URL, "computers/laptops")},
    {"name": "tablets", "url": urljoin(HOME_URL, "computers/tablets")},
    {"name": "phones", "url": urljoin(HOME_URL, "phones")},
    {"name": "touch", "url": urljoin(HOME_URL, "phones/touch")},
]


class Driver:
    def __init__(self) -> None:
        self._driver = None

    @property
    def driver(self) -> None | Chrome:
        return self._driver

    @driver.setter
    def driver(self, new_driver: Chrome) -> None:
        self._driver = new_driver


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


PRODUCT_FIELDS = [field.name for field in fields(Product)]


def add_driver_options() -> webdriver.ChromeOptions:
    options = webdriver.ChromeOptions()
    options.add_argument("--incognito")
    options.add_argument("--headless")
    return options


def parse_single_product(product_soup: Tag) -> Product:
    rating = product_soup.select_one("p[data_rating]")
    return Product(
        title=product_soup.select_one(".title")["title"],
        description=normalize(
            "NFKD", product_soup.select_one(".description").text
        ),
        price=float(product_soup.select_one(".price").text.replace("$", "")),
        rating=int(rating["data_rating"]) if rating else 5,
        num_of_reviews=int(product_soup.select_one(
            ".ratings > p.pull-right"
        ).text.split()[0])
    )


def load_all_products_on_page(driver: Chrome, url: str) -> BeautifulSoup:
    driver.get(url)
    try:
        driver.find_element(By.CLASS_NAME, "acceptCookies").click()
    except NoSuchElementException:
        pass
    while True:
        try:
            more_button = driver.find_element(
                By.CLASS_NAME, "ecomerce-items-scroll-more"
            )
            WebDriverWait(driver, 10).until(
                ec.visibility_of_all_elements_located(
                    (By.CLASS_NAME, "thumbnail")
                )
            )
            more_button.click()
        except (NoSuchElementException, ElementNotInteractableException):
            break
    return BeautifulSoup(driver.page_source, "html.parser")


def write_products_to_csv(filename: str, products: list[Product]) -> None:
    with open(filename + ".csv", "w") as file:
        writer = csv.writer(file)
        writer.writerow(PRODUCT_FIELDS)
        writer.writerows([astuple(product) for product in products])


def get_all_products() -> None:
    with webdriver.Chrome(options=add_driver_options()) as new_driver:
        driver = Driver()
        driver.driver = new_driver
        for page in PAGES:
            soup = load_all_products_on_page(
                driver=driver.driver, url=page["url"]
            )
            products_data = soup.select(".thumbnail")
            products = [
                parse_single_product(product) for product in products_data
            ]
            write_products_to_csv(page["name"], products)


if __name__ == "__main__":
    get_all_products()
