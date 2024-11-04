import csv
from dataclasses import dataclass, fields, astuple
from enum import Enum
from time import sleep
from urllib.parse import urljoin

from bs4 import BeautifulSoup, Tag
from selenium import webdriver
from selenium.common import (
    NoSuchElementException,
    TimeoutException,
    ElementNotInteractableException,
    ElementClickInterceptedException
)
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from tqdm import tqdm


BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")


class URLS(Enum):
    HOME = HOME_URL
    COMPUTERS = urljoin(HOME_URL, "computers/")
    LAPTOPS = urljoin(HOME_URL, "computers/laptops")
    TABLETS = urljoin(HOME_URL, "computers/tablets")
    PHONES = urljoin(HOME_URL, "phones/")
    TOUCH = urljoin(HOME_URL, "phones/touch")


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


PRODUCT_FIELDS = [field.name for field in fields(Product)]


def get_webdriver() -> webdriver.Chrome:
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    driver = webdriver.Chrome(options=chrome_options)
    # driver = webdriver.Chrome()
    return driver


def get_single_product(soup: Tag) -> Product:
    return Product(
        title=soup.select_one(".title")["title"],
        description=soup.select_one(".description").text,
        price=float(soup.select_one(".price").text.replace("$", "")),
        rating=len(soup.select(".ws-icon-star")),
        num_of_reviews=int(soup.select_one(".review-count").text.split()[0])
    )


def get_products(driver: webdriver.Chrome, url: str) -> list[Product]:
    driver.get(url)

    try:
        while True:
            sleep(2)
            button = driver.find_element(By.CLASS_NAME, "ecomerce-items-scroll-more")
            button.click()
            WebDriverWait(driver, 2).until(
                ec.presence_of_all_elements_located(
                    (By.CLASS_NAME, "card-body"))
            )

    except (
        TimeoutException,
        NoSuchElementException,
        ElementClickInterceptedException,
        ElementNotInteractableException
    ):
        pass

    soup = BeautifulSoup(driver.page_source, "html.parser")

    return [
        get_single_product(product_soup)
        for product_soup in soup.select(".card-body")
    ]


def write_products_to_csv(products: list[Product], path: str) -> None:
    with open(path, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(PRODUCT_FIELDS)
        writer.writerows([astuple(product) for product in products])


def get_all_products() -> None:
    driver = get_webdriver()

    for url in tqdm(URLS):
        products = get_products(driver, url.value)
        write_products_to_csv(products, f"{url.name.lower()}.csv")

    driver.quit()


if __name__ == "__main__":
    get_all_products()
