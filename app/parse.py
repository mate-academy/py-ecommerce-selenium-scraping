import csv
from dataclasses import dataclass, fields, astuple
import time
from urllib.parse import urljoin
from bs4 import BeautifulSoup, Tag
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium import webdriver
from selenium.webdriver.common.by import By

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")
LAPTOP_URL = HOME_URL + "computers/tablets"
PRODUCT_URLS = {
    "home": HOME_URL,
    "computers": urljoin(HOME_URL, "computers"),
    "laptops": urljoin(HOME_URL, "computers/laptops"),
    "tablets": urljoin(HOME_URL, "computers/tablets"),
    "phones": urljoin(HOME_URL, "phones"),
    "touch": urljoin(HOME_URL, "phones/touch"),
}


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int
    additional_info: dict


PRODUCT_FIELDS = [field.name for field in fields(Product)]

_driver: WebDriver | None = None


def get_driver() -> WebDriver:
    return _driver


def set_driver(new_driver: WebDriver) -> None:
    global _driver
    _driver = new_driver


def parse_additional_info(product_soup: Tag) -> dict[str, float]:
    detailed_url = urljoin(BASE_URL, product_soup.select_one(".title")["href"])
    driver = get_driver()
    driver.get(detailed_url)
    try:
        swatches = driver.find_element(By.CLASS_NAME, "swatches")
        buttons = swatches.find_elements(By.TAG_NAME, "button")
        add_info = {}
        for button in buttons:
            if not button.get_property("disabled"):
                button.click()
                add_info[
                    button.get_property("value")
                ] = float(driver.find_element(
                    By.CLASS_NAME, "price"
                ).text.replace("$", ""))
    except NoSuchElementException:
        colors = driver.find_elements(By.TAG_NAME, "option")
        add_info = [color.get_property("value") for color in colors][1:]
    return add_info


def parse_single_product(product_soup: Tag) -> Product:
    additional_info = parse_additional_info(product_soup)
    return Product(
        title=product_soup.select_one(".title")["title"],
        description=product_soup.select_one(".description").text,
        price=float(product_soup.select_one(".price").text.replace("$", "")),
        rating=len(product_soup.select(".glyphicon-star")),
        num_of_reviews=int(
            product_soup.select_one(".ratings > p.pull-right").text.split()[0]
        ),
        additional_info=additional_info,
    )


def accept_cookies(driver: WebDriver) -> None:
    try:
        accept = driver.find_element(By.CLASS_NAME, "acceptCookies")
        accept.click()
    except NoSuchElementException:
        pass


def load_page(driver: WebDriver) -> None:
    driver.maximize_window()
    try:
        more = driver.find_element(By.CLASS_NAME, "ecomerce-items-scroll-more")
        while more.is_displayed():
            more.click()
            time.sleep(1)
    except NoSuchElementException:
        pass


def parse_single_page(url: str) -> list[Product]:
    driver = get_driver()
    driver.get(PRODUCT_URLS[url])
    accept_cookies(driver)
    load_page(driver)
    page = driver.page_source
    soup = BeautifulSoup(page, "html.parser")
    products = soup.select(".thumbnail")
    return [parse_single_product(product_soup) for product_soup in products]


def write_products_to_csv(url: str, products: list[Product]) -> None:
    with open(f"{url}.csv", "w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(PRODUCT_FIELDS)
        writer.writerows([astuple(product) for product in products])


def get_all_products() -> None:
    with webdriver.Chrome() as new_driver:
        set_driver(new_driver)
        for url in PRODUCT_URLS:
            products = parse_single_page(url)
            write_products_to_csv(url, products)


if __name__ == "__main__":
    get_all_products()
