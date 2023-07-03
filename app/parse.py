import csv
from dataclasses import dataclass, astuple
from urllib.parse import urljoin
from selenium import webdriver
from selenium.common import (
    NoSuchElementException,
    ElementNotInteractableException
)
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")
PHONES_URL = HOME_URL + "phones"
TOUCH_URL = HOME_URL + "phones/touch"
COMPUTERS_URL = HOME_URL + "computers"
TABLETS_URL = HOME_URL + "computers/tablets"
LAPTOPS_URL = HOME_URL + "computers/laptops"

FILENAME_URL_MAP = {
    PHONES_URL: "phones.csv",
    TOUCH_URL: "touch.csv",
    COMPUTERS_URL: "computers.csv",
    TABLETS_URL: "tablets.csv",
    LAPTOPS_URL: "laptops.csv",
    HOME_URL: "home.csv",
}


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


def write_products_to_csv(output_csv_path: str, products: [Product]) -> None:
    with open(output_csv_path, "w", encoding="utf-8", newline="") as file:
        header = ["title", "description", "price", "rating", "num_of_reviews"]
        writer = csv.writer(file)
        writer.writerow(header)
        writer.writerows([astuple(product) for product in products])


def parse_single_product(element: WebElement) -> Product:
    return Product(
        title=element.find_element
        (By.CLASS_NAME, "title").get_attribute("title"),
        description=element.find_element(By.CLASS_NAME, "description").text,
        price=float(element.find_element(
            By.CLASS_NAME, "price").text.replace("$", "")),
        rating=int(len(element.find_elements(
            By.CSS_SELECTOR, "div.ratings > p:nth-child(2) > span"))),
        num_of_reviews=int(element.find_element(
            By.CSS_SELECTOR, ".ratings > p").text.split()[0])
    )


def get_products_from_page(driver: WebDriver) -> [Product]:
    try:
        banner = driver.find_element(By.ID, "cookieBanner")
        banner.find_element(By.CLASS_NAME, "acceptCookies").click()
    except NoSuchElementException:
        pass

    while True:
        try:
            driver.find_element(
                By.CLASS_NAME, "ecomerce-items-scroll-more").click()
        except (ElementNotInteractableException, NoSuchElementException):
            break

    products = driver.find_elements(By.CLASS_NAME, "thumbnail")
    return [parse_single_product(product) for product in products]


def get_all_products() -> None:
    with webdriver.Chrome() as driver:
        for url, filename in FILENAME_URL_MAP.items():
            driver.get(url)
            products = get_products_from_page(driver)
            write_products_to_csv(filename, products)


if __name__ == "__main__":
    get_all_products()
