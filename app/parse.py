import csv
from dataclasses import astuple, dataclass, fields
from time import sleep
from urllib.parse import urljoin

from bs4 import BeautifulSoup, Tag
from selenium import webdriver
from selenium.common import (ElementClickInterceptedException,
                             ElementNotInteractableException,
                             NoSuchElementException)
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from tqdm import tqdm

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")

PAGES = {
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


PRODUCT_FIELDS = [field.name for field in fields(Product)]


def get_driver() -> webdriver.Chrome:
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    return webdriver.Chrome(options=options)


def accept_cookies(driver: webdriver.Chrome) -> None:
    try:
        cookies_button = driver.find_element(
            By.CLASS_NAME,
            "t-acceptAllButton"
        )
        cookies_button.click()
    except NoSuchElementException:
        pass


def click_more_button(driver: webdriver.Chrome) -> None:
    while True:
        try:
            more_button = driver.find_element(
                By.CLASS_NAME, "ecomerce-items-scroll-more"
            )
        except NoSuchElementException:
            break

        try:
            more_button.click()
            sleep(0.3)
        except (
            ElementNotInteractableException,
            ElementClickInterceptedException,
        ):
            break


def parse_single_product(product: Tag) -> Product:
    return Product(
        title=product.select_one(".title")["title"],
        description=product.select_one(
            ".description"
        ).text.replace("\xa0", " "),
        price=float(product.select_one(".price").text.replace("$", "")),
        rating=len(product.select(".ratings p:not(.review-count) span")),
        num_of_reviews=int(product.select_one(
            "span[itemprop='reviewCount']"
        ).text),
    )


def get_single_page_products(
        driver: webdriver.Chrome,
        url: str
) -> list[Product]:
    driver.get(url)
    accept_cookies(driver)
    click_more_button(driver)

    page_soup = BeautifulSoup(driver.page_source, "html.parser")
    products_soup = page_soup.select(".thumbnail")

    return [parse_single_product(product) for product in products_soup]


def write_products_to_csv(products: list[Product], file_name: str) -> None:
    with open(f"{file_name}.csv", "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(PRODUCT_FIELDS)
        writer.writerows([astuple(product) for product in products])


def get_all_products() -> None:
    with get_driver() as driver:
        for file_name, url in tqdm(PAGES.items(), desc="Parsing pages"):
            products = get_single_page_products(driver, url)
            write_products_to_csv(products, file_name)


if __name__ == "__main__":
    get_all_products()
