import csv
import time
from dataclasses import dataclass, fields, astuple
from typing import List
from urllib.parse import urljoin

from bs4 import BeautifulSoup, Tag
from selenium import webdriver
from selenium.common import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By


BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")

URLS = {
    "home": HOME_URL,
    "computers": urljoin(HOME_URL, "computers"),
    "phones": urljoin(HOME_URL, "phones"),
    "laptops": urljoin(HOME_URL, "computers/laptops"),
    "tablets": urljoin(HOME_URL, "computers/tablets"),
    "touch": urljoin(HOME_URL, "phones/touch")
}


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


PRODUCT_FIELD = [field.name for field in fields(Product)]


def parse_single_product(product_soup: Tag) -> Product:
    return Product(
        title=product_soup.select_one(".title")["title"],
        description=product_soup.select_one(
            ".description"
        ).text.replace("\xa0", " "),
        price=float(product_soup.select_one(".price").text[1:]),
        rating=len(product_soup.select(".glyphicon-star")),
        num_of_reviews=int(
            product_soup.select_one("p.pull-right").text.split()[0]
        ),
    )


def parse_products(url: str, driver: webdriver) -> List[Product]:
    driver.get(url)
    try:
        driver.find_element(By.CLASS_NAME, "acceptCookies").click()
    except NoSuchElementException:
        pass
    try:
        more_button = driver.find_elements(
            By.CLASS_NAME,
            "ecomerce-items-scroll-more"
        )
        while more_button and more_button[0].is_displayed():
            more_button[0].click()
            time.sleep(0.1)
    except TimeoutException as e:
        print(f"Timed out waiting for 'More' button: {e}")
    finally:
        soup = BeautifulSoup(driver.page_source, "html.parser")
        products = soup.select(".thumbnail")

    return [parse_single_product(product) for product in products]


def write_in_files(output_csv_path: str, url: str, driver: webdriver) -> None:
    with open(output_csv_path, "w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(PRODUCT_FIELD)
        products = parse_products(url, driver)
        writer.writerows([astuple(product) for product in products])


def get_all_products() -> None:
    with webdriver.Chrome() as driver:
        for name, url in URLS.items():
            write_in_files(f"{name}.csv", url, driver)


if __name__ == "__main__":
    get_all_products()
