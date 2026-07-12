import csv
import time
from dataclasses import astuple, dataclass, fields
from urllib.parse import urljoin

from bs4 import BeautifulSoup, Tag
from selenium import webdriver
from selenium.common.exceptions import (
    ElementNotInteractableException,
    NoSuchElementException,
)
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By


BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")

URLS = {
    "home": HOME_URL,
    "computers": urljoin(HOME_URL, "computers"),
    "laptops": urljoin(HOME_URL, "computers/laptops"),
    "tablets": urljoin(HOME_URL, "computers/tablets"),
    "phones": urljoin(HOME_URL, "phones"),
    "touch": urljoin(HOME_URL, "phones/touch"),
}

PAGES_WITH_PAGINATION = ("laptops", "tablets", "touch")


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


PRODUCT_FIELDS = [field.name for field in fields(Product)]


def get_new_driver() -> WebDriver:
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")

    return webdriver.Chrome(options=options)


def accept_cookies(driver: WebDriver) -> None:
    try:
        cookies_button = driver.find_element(By.CLASS_NAME, "acceptCookies")
        cookies_button.click()
    except (NoSuchElementException, ElementNotInteractableException):
        pass


def click_all_more_buttons(driver: WebDriver) -> None:
    while True:
        try:
            more_button = driver.find_element(
                By.CLASS_NAME, "ecomerce-items-scroll-more"
            )
        except NoSuchElementException:
            break

        if not more_button.is_displayed():
            break

        try:
            more_button.click()
        except ElementNotInteractableException:
            break

        time.sleep(0.2)


def parse_single_product(product_soup: Tag) -> Product:
    title = str(product_soup.select_one(".title")["title"])
    description = product_soup.select_one(".description").text.replace(
        "\xa0", " "
    )
    price = float(product_soup.select_one(".price").text.replace("$", ""))
    rating = int(product_soup.select_one("p[data-rating]")["data-rating"])
    reviews_text = product_soup.select_one(".ratings > p.pull-right").text
    num_of_reviews = int(reviews_text.split()[0])

    return Product(
        title=title,
        description=description,
        price=price,
        rating=rating,
        num_of_reviews=num_of_reviews,
    )


def get_single_page_products(
    driver: WebDriver, url: str, needs_pagination: bool
) -> list[Product]:
    driver.get(url)
    accept_cookies(driver)

    if needs_pagination:
        click_all_more_buttons(driver)

    soup = BeautifulSoup(driver.page_source, "html.parser")
    product_soups = soup.select(".thumbnail")

    return [
        parse_single_product(product_soup) for product_soup in product_soups
    ]


def write_products_to_csv(products: list[Product], file_path: str) -> None:
    with open(file_path, "w", newline="", encoding="utf-8") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(PRODUCT_FIELDS)
        writer.writerows([astuple(product) for product in products])


def get_all_products() -> None:
    driver = get_new_driver()

    try:
        for page_name, url in URLS.items():
            products = get_single_page_products(
                driver, url, page_name in PAGES_WITH_PAGINATION
            )
            write_products_to_csv(products, f"{page_name}.csv")
    finally:
        driver.quit()


if __name__ == "__main__":
    get_all_products()
