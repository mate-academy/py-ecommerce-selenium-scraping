from dataclasses import dataclass, fields, astuple
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup
import csv
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.common.exceptions import (
    TimeoutException,
    ElementNotInteractableException
)
from tqdm import tqdm


BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")
COMPUTERS_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/computers")
LAPTOPS_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/computers/laptops")
TABLETS_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/computers/tablets")
PHONES_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/phones")
TOUCH_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/phones/touch")


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


HOME_OUTPUT_CSV_PATH = "home.csv"
COMPUTER_OUTPUT_CSV_PATH = "computers.csv"
LAPTOPS_OUTPUT_CSV_PATH = "laptops.csv"
TABLETS_OUTPUT_CSV_PATH = "tablets.csv"
PHONES_OUTPUT_CSV_PATH = "phones.csv"
TOUCH_OUTPUT_CSV_PATH = "touch.csv"

PRODUCT_FIELDS = [field.name for field in fields(Product)]


def write_products_to_csv(products: [Product], path: str) -> None:
    with open(path, "w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(PRODUCT_FIELDS)
        writer.writerows([astuple(product) for product in products])


def accept_cookie(driver: webdriver) -> None:
    try:
        WebDriverWait(driver, 10).until(
            ec.visibility_of_element_located(
                (By.CLASS_NAME, "acceptCookies")
            )
        )
        WebDriverWait(driver, 10).until(
            ec.element_to_be_clickable(
                (By.CLASS_NAME, "acceptCookies")
            )
        ).click()
        print("COOKIE button clicked")
    except (TimeoutException, ElementNotInteractableException):
        pass


def load_page(driver: webdriver) -> None:
    WebDriverWait(driver, 10).until(
        ec.visibility_of_element_located(
            (
                By.CLASS_NAME,
                "ecomerce-items-scroll-more"
            )
        )
    )
    while True:
        try:
            driver.execute_script(
                "arguments[0].click();",
                WebDriverWait(driver, 10).until(
                    ec.element_to_be_clickable(
                        (
                            By.CLASS_NAME,
                            "ecomerce-items-scroll-more"
                        )
                    )
                )
            )
        except (TimeoutException, ElementNotInteractableException):
            break


def get_single_page_products(page: BeautifulSoup, page_name: str) -> [Product]:
    print(f"Collecting {page_name} page")
    products = []
    for product in tqdm(page.select(".card-body")):
        products.append(
            Product(
                title=product.select_one(".title")["title"],
                description=product.select_one(".description").text,
                price=float(
                    product.select_one(".price").text.replace("$", "")
                ),
                rating=int(
                    product.select_one(".review-count + p")["data-rating"]
                ),
                num_of_reviews=int(
                    product.select_one(".review-count").text.split()[0]
                ),
            )
        )
    return products


def get_single_page_with_more_button(
    driver: webdriver,
    page_name: str
) -> [Product]:
    print(f"Collecting {page_name} page")
    accept_cookie(driver)
    load_page(driver)
    products = []
    for product in tqdm(driver.find_elements(By.CLASS_NAME, "card-body")):
        products.append(
            Product(
                title=product.find_element(
                    By.CLASS_NAME,
                    "title"
                ).get_attribute("title"),
                description=product.find_element(
                    By.CLASS_NAME,
                    "description"
                ).text,
                price=float(product.find_element(
                    By.CLASS_NAME,
                    "price"
                ).text.replace("$", "")),
                rating=len(product.find_elements(
                    By.CSS_SELECTOR,
                    ".review-count + p > span"
                )),
                num_of_reviews=int(
                    product.find_element(
                        By.CLASS_NAME,
                        "review-count"
                    ).text.split()[0]
                ),
            )
        )
    return products


def get_home_page() -> [Product]:
    page = requests.get(HOME_URL).content
    soup = BeautifulSoup(page, "html.parser")

    return write_products_to_csv(
        get_single_page_products(soup, "home"),
        HOME_OUTPUT_CSV_PATH
    )


def get_computers() -> [Product]:
    page = requests.get(COMPUTERS_URL).content
    soup = BeautifulSoup(page, "html.parser")

    return write_products_to_csv(
        get_single_page_products(soup, "computers"),
        COMPUTER_OUTPUT_CSV_PATH
    )


def get_laptops(driver: webdriver) -> None:
    driver.get(LAPTOPS_URL)

    return write_products_to_csv(
        get_single_page_with_more_button(driver, "laptops"),
        LAPTOPS_OUTPUT_CSV_PATH
    )


def get_tablets(driver: webdriver) -> None:
    driver.get(TABLETS_URL)

    return write_products_to_csv(
        get_single_page_with_more_button(driver, "tablets"),
        TABLETS_OUTPUT_CSV_PATH
    )


def get_phones() -> [Product]:
    page = requests.get(PHONES_URL).content
    soup = BeautifulSoup(page, "html.parser")

    return write_products_to_csv(
        get_single_page_products(soup, "phones"),
        PHONES_OUTPUT_CSV_PATH
    )


def get_touch(driver: webdriver) -> None:
    driver.get(TOUCH_URL)

    return write_products_to_csv(
        get_single_page_with_more_button(driver, "touch"),
        TOUCH_OUTPUT_CSV_PATH
    )


def get_all_products() -> None:
    options = webdriver.ChromeOptions()
    options.add_argument("headless")
    with webdriver.Chrome(options=options) as driver:
        get_home_page()
        get_computers()
        get_laptops(driver)
        get_tablets(driver)
        get_phones()
        get_touch(driver)


if __name__ == "__main__":
    get_all_products()
