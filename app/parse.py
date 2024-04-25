import csv
from dataclasses import dataclass, fields, astuple
from urllib.parse import urljoin

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.ui import WebDriverWait
from tqdm import tqdm

from bs4 import BeautifulSoup

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


FIELDS_NAME = [field.name for field in fields(Product)]
URLS = {
    "home": HOME_URL,
    "computers": "test-sites/e-commerce/more/computers",
    "laptops": "test-sites/e-commerce/more/computers/laptops",
    "tablets": "test-sites/e-commerce/more/computers/tablets",
    "phones": "test-sites/e-commerce/more/phones",
    "touch": "test-sites/e-commerce/more/phones/touch"
}


def parse_single_product(soup: BeautifulSoup) -> Product:
    return Product(
        title=soup.select_one(".title")["title"],
        description=soup.select_one(".description").text.replace(" ", " "),
        price=float(soup.select_one(".price").text.replace("$", "")),
        rating=len(soup.select(".ws-icon")),
        num_of_reviews=int(soup.select_one(".review-count").text.split()[0]),
    )


def get_single_page_products(page_soup: BeautifulSoup) -> [Product]:
    products = page_soup.select(".thumbnail")
    return [parse_single_product(product_soup) for product_soup in products]


def write_products_to_csv(products: [Product], filename: str) -> None:
    with open(filename, "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(FIELDS_NAME)
        writer.writerows([astuple(product) for product in products])


def confirm_cookies(driver: webdriver.Chrome) -> None:
    while True:
        try:
            accept = WebDriverWait(driver, 5).until(
                expected_conditions.element_to_be_clickable(
                    (By.CLASS_NAME, "acceptCookies")
                )
            )
            accept.click()
        except Exception:
            break


def load_products(driver: webdriver.Chrome) -> None:
    while True:
        try:
            more_btn = WebDriverWait(driver, 5).until(
                expected_conditions.element_to_be_clickable(
                    (By.CSS_SELECTOR, ".btn.ecomerce-items-scroll-more")
                )
            )
            more_btn.click()
        except Exception:
            break


def get_all_products() -> [Product]:
    options = Options()
    options.add_argument("--headless")
    with webdriver.Chrome(options=options) as driver:
        for name, url in tqdm(URLS.items()):
            print(f"Parsing {name} page")
            driver.get(urljoin(BASE_URL, url))
            load_products(driver)
            confirm_cookies(driver)
            soup = BeautifulSoup(driver.page_source, "html.parser")
            all_products = get_single_page_products(soup)
            write_products_to_csv(
                products=all_products,
                filename=f"{name}.csv"
            )


if __name__ == "__main__":
    get_all_products()
