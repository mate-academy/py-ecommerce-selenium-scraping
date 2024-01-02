import csv
import time

from selenium.webdriver.remote.webdriver import WebDriver
from dataclasses import dataclass, astuple, fields
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium import webdriver


BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")

PRODUCT_PAGES = {
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


PRODUCT_FIELDS = [field.name for field in fields(Product)]


def get_driver() -> WebDriver:
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    driver = webdriver.Chrome(options=options)
    return driver


def parse_single_product(product_soup: BeautifulSoup) -> Product:
    return Product(
        title=product_soup.select_one("a.title")["title"],
        description=product_soup.select_one("p.description").text.replace(
            "\xa0", " "
        ),
        price=float(product_soup.select_one("h4.price").text.replace("$", "")),
        rating=len(product_soup.select(".ws-icon-star")),
        num_of_reviews=int(
            product_soup.select_one("p.review-count").text.split()[0]
        ),
    )


def get_single_page_products(
    page_url: str, driver: WebDriver
) -> list[Product]:
    driver.get(page_url)
    cookies_button = driver.find_elements(By.CLASS_NAME, "acceptCookies")
    if cookies_button:
        cookies_button[0].click()

    more_button = driver.find_elements(
        By.CLASS_NAME, "ecomerce-items-scroll-more"
    )

    if more_button:
        more_button = more_button[0]
        while more_button.is_displayed():
            more_button.click()
            time.sleep(1)

    page_soup = BeautifulSoup(driver.page_source, "html.parser")

    products = page_soup.select(".thumbnail")
    return [parse_single_product(product_soup) for product_soup in products]


def write_products_to_csv(
    products: list[Product], output_csv_path: str
) -> None:
    with open(output_csv_path, "w", newline="", encoding="utf-8") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(PRODUCT_FIELDS)
        writer.writerows([astuple(product) for product in products])


def get_all_products() -> None:
    with get_driver() as new_driver:
        for name, page_url in PRODUCT_PAGES.items():
            print(f"Getting {name} products from {page_url}")
            all_products = get_single_page_products(page_url, new_driver)
            write_products_to_csv(all_products, f"{name}.csv")


if __name__ == "__main__":
    get_all_products()
