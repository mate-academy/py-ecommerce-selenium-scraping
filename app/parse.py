import logging
import sys
import csv
import time

from dataclasses import dataclass, fields, astuple
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup, Tag

from selenium.webdriver.firefox.webdriver import WebDriver
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.common.exceptions import TimeoutException

from contextlib import contextmanager


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


@contextmanager
def web_driver() -> WebDriver:
    driver = webdriver.Firefox()
    try:
        yield driver
    finally:
        driver.close()


logging.basicConfig(
    level=logging.INFO,
    #  level=logging.DEBUG,
    format="[%(levelname)8s]: %(message)s",
    handlers=[
        logging.FileHandler("parser.log"),
        logging.StreamHandler(sys.stdout),
    ]
)


def write_products_to_csv(products: list[Product], file_name: str) -> None:
    logging.info(f"Save data from subcatalogy into {file_name}")
    with open(file_name, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(PRODUCT_FIELDS)
        writer.writerows([astuple(product) for product in products])


def get_single_product(product_soup: Tag) -> Product:
    return Product(
        title=product_soup.select_one(".title")["title"],
        description=product_soup.select_one(
            ".description").text.replace("\xa0", " "),
        price=float(product_soup.select_one(".price").text.replace("$", "")),
        rating=len(product_soup.select(".ws-icon-star")),
        num_of_reviews=int(
            product_soup.select_one(".review-count").text.split()[0]
        ),
    )


def get_all_products_on_page(driver: WebDriver, url: str) -> list[Product]:
    list_products = []
    html = driver.page_source
    part_page_soup = BeautifulSoup(html, "html.parser")
    products_soup = part_page_soup.select_one(".ecomerce-items-more")
    products_list_soup = products_soup.select(".col-md-4")
    logging.info(
        f"Total found {len(products_list_soup)} products on this page"
    )
    for product in products_list_soup:
        list_products.append(get_single_product(product))
    return list_products


def get_one_page_of_products(driver: WebDriver, subcategory_link: str) -> None:
    url = urljoin(BASE_URL, subcategory_link)
    logging.info(f"Start parsing subcatalogy page: {url}")
    driver.get(url)

    wait = WebDriverWait(driver, 10)
    try:
        link_more = wait.until(ec.element_to_be_clickable(
            (By.CSS_SELECTOR, "a.ecomerce-items-scroll-more")
        ))

        logging.info(f"subcategory: {subcategory_link.split("/")[-1]}")
        while link_more:
            time.sleep(1)
            link_more.click()
            print(".", end="")
            try:
                link_more = wait.until(ec.element_to_be_clickable(
                    (By.CSS_SELECTOR, "a.ecomerce-items-scroll-more")
                ))
            except TimeoutException:
                break

    finally:
        file_name = f"{subcategory_link.split("/")[-1]}.csv"
        products = get_all_products_on_page(driver, url)
        logging.info(f"There are  {len(products)} products for save")
        write_products_to_csv(products, file_name)


def get_subcategory_links(driver: WebDriver, category_link: str) -> None:
    url = urljoin(BASE_URL, category_link)
    logging.info(f"Get links from sidebar of catalogy page: {url}")
    text = requests.get(url).content
    catalogy_page_soup = BeautifulSoup(text, "html.parser")

    link_tags = catalogy_page_soup.find_all("a", class_="subcategory-link")

    for link_tag in link_tags:
        if link_tag:
            subcategory_link = link_tag["href"]
            logging.info(
                f"Go to the single page of products: {subcategory_link}"
            )
            get_one_page_of_products(driver, subcategory_link)


def get_category_pages(driver: WebDriver) -> None:
    logging.info(f"Start parsing page: {HOME_URL}")

    # accept cookies
    wait = WebDriverWait(driver, 10)
    button_cookies = wait.until(ec.element_to_be_clickable(
        (By.CSS_SELECTOR, "button.acceptCookies")
    ))
    button_cookies.click()
    logging.info("Accepted cookies")

    text = requests.get(HOME_URL).content
    home_page_soup = BeautifulSoup(text, "html.parser")

    link_tags = home_page_soup.find_all("a", class_="category-link")
    for link_tag in link_tags:
        if link_tag:
            category_link = link_tag["href"]
            file_name = f"{category_link.split("/")[-1]}.csv"
            get_and_save_random_products_on_page(
                driver, urljoin(BASE_URL, category_link), file_name
            )
            logging.info(f"Go to the category link: {category_link}")
            get_subcategory_links(driver, category_link)


def get_and_save_random_products_on_page(
    driver: WebDriver, url: str, file_name: str
) -> None:
    logging.info(f"Start parsing page with random products: {url}")
    text = requests.get(url).content
    page_soup = BeautifulSoup(text, "html.parser")
    products_soup = page_soup.select(".col-md-4")

    products = []
    logging.info(
        f"Total found {len(products_soup)} random products on this page"
    )
    for product in products_soup:
        products.append(get_single_product(product))

    write_products_to_csv(products, file_name)


def get_all_products() -> None:
    with web_driver() as driver:
        logging.info(f"Open driver window: driver = {driver}")
        driver.get(HOME_URL)
        get_and_save_random_products_on_page(driver, HOME_URL, "home.csv")
        get_category_pages(driver)

    logging.info("Closing window")


if __name__ == "__main__":
    get_all_products()
