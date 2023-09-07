import csv
from dataclasses import dataclass, fields, astuple
from time import sleep
from urllib.parse import urljoin
from bs4 import BeautifulSoup, Tag
from selenium import webdriver
from selenium.common import NoSuchElementException
from selenium.webdriver.common.by import By

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")
PHONES_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/phones")
TOUCHES_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/phones/touch")
COMPUTERS_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/computers")
TABLETS_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/computers/tablets")
LAPTOPS_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/computers/laptops")


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


PRODUCT_FIELDS = [field.name for field in fields(Product)]


def parse_single_product(product_soup: Tag) -> Product:
    return Product(
        title=product_soup.select_one(".title")["title"],
        description=product_soup.select_one(
            ".description"
        ).text.replace("\xa0", " "),
        price=float(product_soup.select_one(".price").text.replace("$", "")),
        rating=len(product_soup.select(".ws-icon.ws-icon-star")),
        num_of_reviews=int(
            product_soup.select_one("p.pull-right").text.split()[0]
        )
    )


def get_product_blocks(page_soup: BeautifulSoup) -> list[Tag]:
    blocks = page_soup.select(".thumbnail")
    return [block for block in blocks]


def accept_cookies(driver: webdriver) -> None:
    try:
        cookie_button = driver.find_element(
            By.CLASS_NAME, "acceptCookies"
        )
        cookie_button.click()
    except NoSuchElementException:
        pass


def parse_single_page(url: str, driver: webdriver) -> list[Product]:
    driver.get(url)
    accept_cookies(driver)

    try:
        more_button = driver.find_element(
            By.CSS_SELECTOR,
            "a.btn.btn-primary.btn-lg.btn-block.ecomerce-items-scroll-more"
        )
        while more_button.is_displayed():
            more_button.click()
            sleep(0.25)

    except NoSuchElementException:
        pass

    soup = BeautifulSoup(driver.page_source, "html.parser")

    products = [
        parse_single_product(block)
        for block
        in get_product_blocks(soup)
    ]

    return products


def write_to_csv(filename: str, products: list[Product]) -> None:
    with open(filename, "w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(PRODUCT_FIELDS)
        writer.writerows([astuple(product) for product in products])


def get_all_products() -> None:
    all_products = {
        "home.csv": HOME_URL,
        "computers.csv": COMPUTERS_URL,
        "laptops.csv": LAPTOPS_URL,
        "tablets.csv": TABLETS_URL,
        "phones.csv": PHONES_URL,
        "touch.csv": TOUCHES_URL
    }
    with webdriver.Chrome() as driver:
        for key, value in all_products.items():
            filename = key
            products = parse_single_page(value, driver)
            write_to_csv(filename=filename, products=products)


if __name__ == "__main__":
    get_all_products()
