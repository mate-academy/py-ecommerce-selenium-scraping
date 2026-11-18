import csv
import dataclasses
import time
from dataclasses import dataclass, astuple
from urllib.parse import urljoin

from bs4 import BeautifulSoup, Tag
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from tqdm import tqdm

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")

PAGES = {
    "home": "",
    "computers": "computers",
    "laptops": "computers/laptops",
    "tablets": "computers/tablets",
    "phones": "phones",
    "touch": "phones/touch",
}

CARDS_SELECTOR = ".card.thumbnail"

_driver: WebDriver | None = None


def get_driver() -> WebDriver | None:
    return _driver


def set_driver(driver: WebDriver | None) -> None:
    global _driver
    _driver = driver


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


PRODUCT_FIELDS = [field.name for field in dataclasses.fields(Product)]


def create_driver() -> WebDriver:
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--window-size=1920,1080")
    return webdriver.Chrome(options=options)


def load_all_items(driver: WebDriver) -> None:
    while True:
        buttons = driver.find_elements(By.CLASS_NAME, "ecomerce-items-scroll-more")
        if not buttons or not buttons[0].is_displayed():
            break
        driver.execute_script("arguments[0].click();", buttons[0])
        time.sleep(0.5)


def get_soup(url: str) -> BeautifulSoup:
    driver = get_driver()
    driver.get(url)
    load_all_items(driver)
    return BeautifulSoup(driver.page_source, "html.parser")


def parse_single_product(product: Tag) -> Product:
    return Product(
        title=product.select_one(".title")["title"],
        description=product.select_one(".description").text.replace("\xa0", " "),
        price=float(product.select_one(".price").text.replace("$", "")),
        rating=len(product.select(".ratings .ws-icon-star")),
        num_of_reviews=int(product.select_one(".review-count").text.split()[0]),
    )


def parse_page(name: str, url: str) -> list[Product]:
    soup = get_soup(url)
    cards = soup.select(CARDS_SELECTOR)
    return [
        parse_single_product(card)
        for card in tqdm(cards, desc=f"Products on '{name}'", leave=False)
    ]


def write_products_to_csv(file_name: str, products: list[Product]) -> None:
    with open(f"{file_name}.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(PRODUCT_FIELDS)
        writer.writerows(astuple(product) for product in products)


def get_all_products() -> None:
    with create_driver() as driver:
        set_driver(driver)
        for name, path in tqdm(PAGES.items(), desc="Pages"):
            products = parse_page(name, urljoin(HOME_URL, path))
            write_products_to_csv(name, products)
            tqdm.write(f"Saved {len(products)} products to {name}.csv")


if __name__ == "__main__":
    get_all_products()
