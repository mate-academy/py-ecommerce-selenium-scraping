import csv
from dataclasses import astuple, dataclass, fields
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")
COMPUTER_URL = "https://webscraper.io/test-sites/e-commerce/more/computers"
LAPTOP_URL = (
    "https://webscraper.io/test-sites/e-commerce/more/computers/laptops"
)
TABLET_URL = (
    "https://webscraper.io/test-sites/e-commerce/more/computers/tablets"
)
PHONE_URL = "https://webscraper.io/test-sites/e-commerce/more/phones"
TOUCH_URL = "https://webscraper.io/test-sites/e-commerce/more/phones/touch"


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


PRODUCT_FIELDS = [field.name for field in fields(Product)]


def parse_single_product(product: BeautifulSoup) -> Product:
    return Product(
        title=product.select_one(".title")["title"],
        description=product.select_one(".description").text.replace(
            "\xa0", " "
        ),
        price=float(product.select_one(".price").text.replace("$", "")),
        rating=len(product.select_one(".ratings").select(".ws-icon-star")),
        num_of_reviews=int(
            product.select_one(".review-count").text.split()[0]
        ),
    )


def get_page_products(url: str) -> list:
    text = requests.get(url).content
    soup = BeautifulSoup(text, "html.parser")
    products = soup.select(".card-body")
    return [parse_single_product(product) for product in products]


def get_more_products(url: str, driver: webdriver) -> list:
    driver.get(url)
    more = driver.find_element(By.CLASS_NAME, "ecomerce-items-scroll-more")
    wait = WebDriverWait(driver, 10)
    while True:
        try:
            more = wait.until(
                ec.element_to_be_clickable(
                    (By.CLASS_NAME, "ecomerce-items-scroll-more")
                )
            )
            driver.execute_script("arguments[0].scrollIntoView(true);", more)
            more.click()
            previous_count = len(
                driver.find_elements(By.CLASS_NAME, "card-body")
            )
            wait.until(
                lambda d: len(d.find_elements(By.CLASS_NAME, "card-body"))
                > previous_count
            )

        except NoSuchElementException:
            break
        except TimeoutException:
            break

    elements = driver.find_elements(By.CLASS_NAME, "card-body")
    soup = BeautifulSoup(driver.page_source, "html.parser")
    products = soup.select(".card-body")
    print(len(products))
    print(len(elements))
    return [parse_single_product(product) for product in products]


def write_to_file(books: list[Product], file_name: str) -> None:
    with open(f"{file_name}", "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(PRODUCT_FIELDS)
        writer.writerows([astuple(book) for book in books])


def get_all_products() -> None:
    write_to_file(get_page_products(HOME_URL), "home.csv")
    write_to_file(get_page_products(COMPUTER_URL), "computers.csv")
    write_to_file(get_page_products(PHONE_URL), "phones.csv")
    with webdriver.Chrome() as driver:
        write_to_file(get_more_products(LAPTOP_URL, driver), "laptops.csv")
        write_to_file(get_more_products(TABLET_URL, driver), "tablets.csv")
        write_to_file(get_more_products(TOUCH_URL, driver), "touch.csv")


if __name__ == "__main__":
    get_all_products()
