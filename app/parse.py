import csv
from dataclasses import dataclass, astuple, fields
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common import NoSuchElementException
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

PRODUCTS_CSV_PATHS = {
    "home": "home.csv",
    "computers": "computers.csv",
    "laptops": "laptops.csv",
    "tablets": "tablets.csv",
    "phones": "phones.csv",
    "touch": "touch.csv",
}


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


def parse_single_product(product_soup: BeautifulSoup) -> Product:
    return Product(
        title=product_soup.select_one(".title")["title"],
        description=product_soup.select_one(
            ".description").text.replace("\xa0", " "),
        price=float(product_soup.select_one(".price").text.replace("$", "")),
        rating=len(product_soup.select(".glyphicon-star")),
        num_of_reviews=int(
            product_soup.select_one(".ratings > p.pull-right").text.split()[0]
        ),
    )


def get_single_page_products(url: str, driver: WebDriver) -> list[Product]:
    driver.get(url)

    try:
        accept_cookies_button = driver.find_element(
            By.CLASS_NAME, "acceptCookies"
        )
        if accept_cookies_button:
            accept_cookies_button.click()
    except NoSuchElementException as e:
        print(f"Unable to locate element{e}")

    try:
        more_button = driver.find_element(
            By.CLASS_NAME, "ecomerce-items-scroll-more"
        )
        if more_button:
            while not more_button.value_of_css_property("display") == "none":
                more_button.click()
    except Exception as e:
        print(f"No such element: {e}")

    page = driver.page_source
    page_soup = BeautifulSoup(page, "html.parser")

    products = page_soup.select(".thumbnail")

    return [parse_single_product(product_soup) for product_soup in products]


def write_products_to_csv(products: list[Product], product_name: str) -> None:
    with open(PRODUCTS_CSV_PATHS[product_name], "w") as file:
        writer = csv.writer(file)
        writer.writerow([field.name for field in fields(Product)])
        writer.writerows(astuple(product) for product in products)


def get_all_products() -> None:
    with webdriver.Chrome() as driver:
        for product_name, path in URLS.items():
            products = get_single_page_products(path, driver)
            write_products_to_csv(products, product_name)


if __name__ == "__main__":
    get_all_products()
