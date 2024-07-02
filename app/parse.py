import csv
import time
from dataclasses import dataclass, fields, astuple
from urllib.parse import urljoin

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from tqdm import tqdm

BASE_URL = "https://webscraper.io/"
URLS = {
    "home": urljoin(BASE_URL, "test-sites/e-commerce/more"),
    "computers": urljoin(BASE_URL, "test-sites/e-commerce/more/computers"),
    "laptops": urljoin(
        BASE_URL, "test-sites/e-commerce/more/computers/laptops"
    ),
    "tablets": urljoin(
        BASE_URL, "test-sites/e-commerce/more/computers/tablets"
    ),
    "phones": urljoin(BASE_URL, "test-sites/e-commerce/more/phones"),
    "touch": urljoin(BASE_URL, "test-sites/e-commerce/more/phones/touch"),
}


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


PRODUCT_FIELDS = [field.name for field in fields(Product)]


def parse_single_product(product: WebElement) -> Product:
    return Product(
        title=product.find_element(
            By.CLASS_NAME, "title"
        ).get_property("title"),
        description=product.find_element(By.CLASS_NAME, "description").text,
        price=float(
            product.find_element(By.CLASS_NAME, "price").text.replace("$", "")
        ),
        rating=len(product.find_elements(By.CLASS_NAME, "ws-icon-star")),
        num_of_reviews=int(
            product.find_element(By.CLASS_NAME, "review-count").text.split()[0]
        ),
    )


def parse_single_page(url: str, driver: webdriver.Chrome) -> list[Product]:
    driver.get(url)

    cookies_button = driver.find_elements(By.CLASS_NAME, "acceptCookies")

    if cookies_button:
        cookies_button[0].click()

    scroll_button = driver.find_elements(
        By.CLASS_NAME, "ecomerce-items-scroll-more"
    )

    if scroll_button:
        while scroll_button[0].is_displayed():
            scroll_button[0].click()
            time.sleep(0.5)

    product_cards = driver.find_elements(By.CLASS_NAME, "card-body")

    products = []

    with tqdm(
        total=len(product_cards),
        desc="Parsing product",
        ncols=100,
    ) as pbar:
        for product in product_cards:
            products.append(parse_single_product(product))
            pbar.update(1)

    return products


def write_to_file(filename: str, products: list[Product]) -> None:
    with open(filename + ".csv", "w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)

        writer.writerow(PRODUCT_FIELDS)
        writer.writerows([astuple(product) for product in products])


def get_all_products() -> None:
    chrome_options = Options()
    chrome_options.add_argument("headless")
    driver = webdriver.Chrome(options=chrome_options)

    with tqdm(
        total=len(URLS),
        desc="Parsing pages",
        ncols=100,
    ) as pbar:
        for name, url in URLS.items():
            all_products = parse_single_page(url, driver)
            write_to_file(name, all_products)
            pbar.update(1)

    driver.quit()


if __name__ == "__main__":
    get_all_products()
