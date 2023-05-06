import csv
import logging
import os
import sys
import time
from tqdm import tqdm
from dataclasses import dataclass, fields, astuple
from urllib.parse import urljoin
from selenium import webdriver
from selenium.common import (
    NoSuchElementException,
    ElementNotInteractableException,
    ElementClickInterceptedException,
)
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


PRODUCT_FIELDS = [field.name for field in fields(Product)]


logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)8s]:  %(message)s",
    handlers=[
        logging.FileHandler(os.path.join("parser.log")),
        logging.StreamHandler(sys.stdout),
    ],
)


def create_single_product(product_data: WebElement) -> Product:
    product = Product(
        title=product_data.find_element(By.CLASS_NAME, "title").get_attribute(
            "title"
        ),
        description=product_data.find_element(
            By.CLASS_NAME, "description"
        ).text,
        price=float(
            product_data.find_element(By.CLASS_NAME, "price").text.replace(
                "$", ""
            )
        ),
        rating=len(
            product_data.find_element(By.CLASS_NAME, "ratings").find_elements(
                By.CLASS_NAME, "glyphicon-star"
            )
        ),
        num_of_reviews=int(
            product_data.find_element(By.CLASS_NAME, "ratings")
            .find_element(By.CLASS_NAME, "pull-right")
            .text.split()[0]
        ),
    )
    logging.info(f"Product has been parsed and created: {product.title}")
    return product


def click_more_button(driver: WebDriver) -> None:
    while True:
        try:
            more_button = driver.find_element(
                By.CLASS_NAME, "ecomerce-items-scroll-more"
            )
            time.sleep(1)
            more_button.click()
        except (
            NoSuchElementException,
            ElementNotInteractableException,
            ElementClickInterceptedException,
        ):
            break


def click_accept_cookies_button(driver: WebDriver) -> None:
    accept_cookie_button = driver.find_element(
        By.ID, "cookieBanner"
    ).find_element(By.CLASS_NAME, "acceptContainer")
    accept_cookie_button.click()


def get_products_single_page(url: str) -> [Product]:
    options = Options()
    options.add_argument("--headless")
    driver = webdriver.Chrome(options=options)

    driver.get(url)
    logging.info(f"Start parsing: {url} page")
    click_accept_cookies_button(driver)
    click_more_button(driver)

    products = driver.find_elements(By.CLASS_NAME, "thumbnail")
    created_products = []
    for product in tqdm(products):
        created_products.append(create_single_product(product))
    return created_products


def get_inside_links(driver: WebDriver, urls: dict) -> dict:
    subcategory_urls = {}
    for url in tqdm(urls.values()):
        driver.get(url)
        additional_links = driver.find_elements(
            By.CLASS_NAME, "subcategory-link "
        )
        for link in tqdm(additional_links):
            subcategory_urls[link.text] = link.get_attribute("href")
    return subcategory_urls


def create_csv_with_page_products(
    filename: str, products: list[Product]
) -> None:
    with open(
        f"{filename.lower()}.csv", "w", encoding="utf-8", newline=""
    ) as file:
        writer = csv.writer(file)
        writer.writerow(PRODUCT_FIELDS)
        writer.writerows([astuple(product) for product in products])
        logging.info(
            f"{filename.lower()}.csv has been created with corresponding items"
        )


def get_all_products() -> None:
    options = Options()
    options.add_argument("--headless")
    driver = webdriver.Chrome(options=options)
    driver.get(HOME_URL)
    sidebar_li_elements = driver.find_elements(
        By.XPATH, '//ul[@id="side-menu"]//li'
    )

    side_bar_hrefs = {}
    logging.info("Starting collected urls of products pages")
    for li_element in tqdm(sidebar_li_elements):
        href_value = li_element.find_element(By.TAG_NAME, "a").get_attribute(
            "href"
        )
        side_bar_hrefs[
            li_element.find_element(By.TAG_NAME, "a").text
        ] = href_value

    side_bar_hrefs.update(get_inside_links(driver, side_bar_hrefs))

    for page in tqdm(side_bar_hrefs):
        create_csv_with_page_products(
            page, get_products_single_page(side_bar_hrefs[page])
        )


if __name__ == "__main__":
    get_all_products()
