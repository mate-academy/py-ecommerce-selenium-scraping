import csv
import logging
import sys
import time
from dataclasses import dataclass, fields, astuple
from typing import NoReturn
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
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


_driver: WebDriver | None = None
PRODUCT_FIELDS = [field.name for field in fields(Product)]


logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)8s]: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)


def get_driver() -> WebDriver:
    return _driver


def set_driver(new_driver: WebDriver) -> None:
    global _driver
    _driver = new_driver


def get_links_to_parse() -> list[str]:
    logging.info("Parsing links")
    driver = get_driver()
    driver.get(HOME_URL)

    sidebar = driver.find_element(By.ID, "side-menu")
    nav_items = sidebar.find_elements(By.CSS_SELECTOR, "[href]")
    links = [link.get_attribute("href") for link in nav_items]

    sub_links = []
    for link in tqdm(links, desc="Main Links", unit="link"):
        driver.get(link)

        subcategory_links = driver.find_elements(
            By.CLASS_NAME, "subcategory-link"
        )
        if subcategory_links:
            for subcategory_link in subcategory_links:
                sub_links.append(subcategory_link.get_attribute("href"))

    links.extend(sub_links)
    return links


def parse_single_product(product_soup: BeautifulSoup) -> Product:
    return Product(
        title=product_soup.select_one(".title")["title"],
        description=product_soup.select_one(".description").text.replace(
            "\xa0", " "
        ),
        price=float(product_soup.select_one(".price").text.replace("$", "")),
        rating=len(product_soup.select(".ws-icon-star")),
        num_of_reviews=int(
            product_soup.select_one(".review-count").text.split()[0]
        ),
    )


def get_soup_products(url: str) -> list:
    logging.info("Parsing products")
    driver = get_driver()
    driver.get(url)

    try:
        cookies_button = WebDriverWait(driver, 10).until(
            ec.element_to_be_clickable((By.CLASS_NAME, "acceptCookies"))
        )
        cookies_button.click()
    except Exception:
        pass

    try:
        more_button = WebDriverWait(driver, 3).until(
            ec.element_to_be_clickable(
                (By.CLASS_NAME, "ecomerce-items-scroll-more")
            )
        )
    except TimeoutException:
        logging.info("No 'Load more' button found.")
        more_button = None

    if more_button:
        while more_button.is_displayed():
            more_button.click()
            time.sleep(1)

    soup = BeautifulSoup(driver.page_source, "html.parser")
    products = soup.select(".card-body")

    return [parse_single_product(product) for product in products]


def get_csv_title(urls: list[str]) -> list[str]:
    return [
        (
            url.split("/")[-1] + ".csv"
            if url.split("/")[-1] != "more"
            else "home.csv"
        )
        for url in urls
    ]


def write_products_to_csv(csv_path: str, products: [Product]) -> NoReturn:
    with open(csv_path, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(PRODUCT_FIELDS)
        writer.writerows([astuple(product) for product in products])


def get_all_products() -> NoReturn:
    options = webdriver.ChromeOptions()
    options.add_argument("headless")

    with webdriver.Chrome(options=options) as new_driver:
        set_driver(new_driver)

        urls = get_links_to_parse()
        titles = get_csv_title(urls)

        for url, title in tqdm(
            zip(urls, titles), desc="Processing Pages", unit="page"
        ):
            products = get_soup_products(url=url)
            write_products_to_csv(title, products)


if __name__ == "__main__":
    get_all_products()
