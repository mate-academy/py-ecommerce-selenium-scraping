import csv
import logging
import sys
import time
from dataclasses import dataclass, fields
from urllib.parse import urljoin
from bs4 import BeautifulSoup, Tag
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By


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


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int

    def to_tuple(self):
        return tuple(getattr(self, field.name) for field in fields(self))


PRODUCT_FIELDS = [field.name for field in fields(Product)]


class ButtonClass:
    ACCEPT_COOKIES_BUTTON = "acceptCookies"
    MORE_BUTTON = "ecomerce-items-scroll-more"


logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)8s]: %(message)s",
    handlers=[
        logging.FileHandler("parser.log"),
        logging.StreamHandler(sys.stdout),
    ],
)


def parse_single_product(product: Tag) -> Product:
    return Product(
        title=product.select_one(".title").get("title").strip(),
        description=product.select_one(".description").text.replace(
            "\xa0", " "
        ),
        price=float(product.select_one(".price").text.replace("$", "")),
        rating=len(product.select(".ratings .glyphicon-star")),
        num_of_reviews=int(
            product.select_one(".ratings > p.pull-right").text.split()[0]
        ),
    )


def get_page_source(url: str, driver: WebDriver) -> str:
    driver.get(url)

    try:
        driver.find_element(
            By.CLASS_NAME, ButtonClass.ACCEPT_COOKIES_BUTTON
        ).click()
    except NoSuchElementException:
        pass

    try:
        more_button = driver.find_element(
            By.CLASS_NAME, ButtonClass.MORE_BUTTON
        )
        while more_button.is_displayed():
            more_button.click()
            time.sleep(0.1)
    except NoSuchElementException:
        pass

    return driver.page_source


def parse_products(page_source: str) -> list[Product]:
    soup = BeautifulSoup(page_source, "html.parser")
    products = soup.select(".thumbnail")
    return [parse_single_product(product) for product in products]


def write_products_to_csv(file_name: str, products: list[Product]) -> None:
    with open(file_name, "w", newline="") as file:
        csv_file = csv.writer(file)
        csv_file.writerow(PRODUCT_FIELDS)
        csv_file.writerows([product.to_tuple() for product in products])


def get_all_products() -> None:
    options = Options()
    options.add_argument("--headless")
    driver = webdriver.Chrome(options=options)

    with driver:
        for page_title, url in URLS.items():
            page = get_page_source(url, driver)
            products = parse_products(page)
            write_products_to_csv(f"{page_title}.csv", products)


if __name__ == "__main__":
    get_all_products()
