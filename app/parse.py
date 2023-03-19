import csv
import logging
import requests
import sys
from dataclasses import dataclass, fields
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common import (
    TimeoutException,
    ElementNotInteractableException,
    ElementClickInterceptedException
)
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions

BASE_URL = "https://webscraper.io/"


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


_driver: WebDriver | None = None


def get_driver() -> WebDriver:
    return _driver


def set_driver(new_driver: WebDriver) -> None:
    global _driver
    _driver = new_driver


logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)8s]: %(message)s",
    handlers=[
        logging.FileHandler("parser.log"),
        logging.StreamHandler(sys.stdout),
    ],
)


def parse_single_product(product_soup: BeautifulSoup) -> Product:
    rating_soup = product_soup.select_one("div.ratings")
    rating_stars = rating_soup.select(".glyphicon.glyphicon-star")
    rating = len(rating_stars)
    description = product_soup.select_one(
        ".description"
    ).text.replace(u"\xa0", u" ")
    return Product(
        title=product_soup.select_one(".title")["title"],
        description=description,
        price=float(product_soup.select_one(".price").text.replace("$", "")),
        rating=rating,
        num_of_reviews=int(
            product_soup.select_one(".ratings > p.pull-right").text.split()[0]
        ),
    )


def get_single_page_products(page_soup: BeautifulSoup) -> [Product]:
    products = page_soup.select(".thumbnail")
    return [parse_single_product(product_soup) for product_soup in products]


def get_all_products() -> None:
    with webdriver.Chrome() as new_driver:
        set_driver(new_driver)
        get_save_products()


def get_save_products() -> None:
    links = get_links()
    for link in links:
        page_link = urljoin(BASE_URL, link)
        logging.info(f"Start parsing {page_link}")
        driver = get_driver()
        driver.get(page_link)
        wait = WebDriverWait(driver, 5)

        try:
            accept_button = wait.until(
                expected_conditions.presence_of_element_located(
                    (By.CLASS_NAME, "acceptCookies")
                )
            )
            if accept_button:
                accept_button.click()
        except TimeoutException:
            pass

        while True:
            try:
                more_button = wait.until(
                    expected_conditions.presence_of_element_located(
                        (By.CSS_SELECTOR, "a.ecomerce-items-scroll-more"))
                )
            except TimeoutException:
                break

            try:
                more_button.click()
                wait.until_not(expected_conditions.staleness_of(more_button))
            except ElementNotInteractableException:
                break
            except ElementClickInterceptedException:
                continue

        all_products = get_single_page_products(
            BeautifulSoup(driver.page_source, "html.parser")
        )

        file_name = link.split("/")[-1] + ".csv"
        if file_name == ".csv":
            file_name = "home.csv"
        write_products_to_csv(all_products, file_name)


def get_links() -> list:
    links = ["test-sites/e-commerce/more/"]
    logging.info("Start parsing links")
    home_url = urljoin(BASE_URL, "test-sites/e-commerce/more/")
    page = requests.get(home_url).content
    page_soup = BeautifulSoup(page, "html.parser")
    category_links = page_soup.select(".category-link")
    for link in category_links:
        href = link.get("href")
        links.append(href)
        follow_page = urljoin(BASE_URL, href)
        follow_page_content = requests.get(follow_page).content
        follow_page_soup = BeautifulSoup(follow_page_content, "html.parser")
        sub_category_links = follow_page_soup.select(".subcategory-link")
        [links.append(link.get("href")) for link in sub_category_links]
    return links


def write_products_to_csv(products: [Product], file_name: str) -> None:
    with open(file_name, "w", newline="", encoding="utf-8") as csvfile:
        field_names = [field.name for field in fields(products[0])]
        writer = csv.DictWriter(csvfile, fieldnames=field_names)
        writer.writeheader()
        for product in products:
            writer.writerow(product.__dict__)


if __name__ == "__main__":
    get_all_products()
