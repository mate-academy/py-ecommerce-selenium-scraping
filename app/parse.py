import csv
import time
from dataclasses import dataclass, fields, astuple
from urllib.parse import urljoin

from selenium import webdriver
from selenium.common import (
    NoSuchElementException,
    ElementNotInteractableException,
)
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup, Tag
from selenium.webdriver.common.by import By
from tqdm import tqdm


BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")

PAGES = {
    "home": HOME_URL,
    "computers": urljoin(HOME_URL, "computers"),
    "phones": urljoin(HOME_URL, "phones"),
    "laptops": urljoin(HOME_URL, "computers/laptops"),
    "tablets": urljoin(HOME_URL, "computers/tablets"),
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


def parse_single_product(product_soup: Tag) -> Product:
    return Product(
        title=product_soup.select_one(".title")["title"],
        description=product_soup.select_one(".description").text,
        price=float(product_soup.select_one(".price").text.replace("$", "")),
        rating=len(product_soup.select(".glyphicon-star")),
        num_of_reviews=int(
            product_soup.select_one("p.pull-right").text.split()[0]
        ),
    )


def get_page_products(
    driver: WebDriver, page_name: str, url: str
) -> list[Product]:
    driver.get(url)

    try:
        cookie_button = driver.find_element(By.CSS_SELECTOR, ".acceptCookies")
        cookie_button.click()
    except NoSuchElementException:
        pass

    while True:
        try:
            more_button = driver.find_element(
                By.CSS_SELECTOR, ".ecomerce-items-scroll-more"
            )
            more_button.click()
            time.sleep(0.1)
        except (ElementNotInteractableException, NoSuchElementException):
            break

    soup = BeautifulSoup(driver.page_source, "html.parser")
    all_products = soup.select(".thumbnail")

    return [
        parse_single_product(product_soup)
        for product_soup in tqdm(all_products, desc=f"Parse {page_name} page")
    ]


def write_products_to_csv(page_name: str, products: list[Product]) -> None:
    with open(
        f"{page_name}.csv", mode="w", newline="", encoding="utf-8"
    ) as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(PRODUCT_FIELDS)
        writer.writerows([astuple(product) for product in products])


def get_all_products() -> None:
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    driver = webdriver.Chrome(options=chrome_options)

    for page_name, page_url in PAGES.items():
        products = get_page_products(driver, page_name, page_url)
        write_products_to_csv(page_name, products)

    driver.quit()


if __name__ == "__main__":
    get_all_products()
