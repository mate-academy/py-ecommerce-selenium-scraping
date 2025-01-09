import csv
import time
from dataclasses import dataclass, fields, astuple
from urllib.parse import urljoin

from bs4 import Tag, BeautifulSoup
from selenium import webdriver
from selenium.common import (
    ElementNotInteractableException,
    NoSuchElementException
)
from selenium.webdriver.common.by import By


BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more")
COMPUTERS_URL = urljoin(f"{HOME_URL}/", "computers")
LAPTOPS_URL = urljoin(f"{COMPUTERS_URL}/", "laptops")
TABLETS_URL = urljoin(f"{COMPUTERS_URL}/", "tablets")
PHONES_URL = urljoin(f"{HOME_URL}/", "phones")
TOUCH_URL = urljoin(f"{PHONES_URL}/", "touch")
URLS = {
    "home": HOME_URL,
    "computers": COMPUTERS_URL,
    "laptops": LAPTOPS_URL,
    "tablets": TABLETS_URL,
    "phones": PHONES_URL,
    "touch": TOUCH_URL,
}


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


PRODUCT_FIELDS = [field.name for field in fields(Product)]


def parse_single_product(product: Tag) -> Product:
    product = Product(
        title=product.select_one(".title")["title"],
        description=product.select_one(".description").text.replace(
            "\xa0", " "
        ),
        price=float(
            product.select_one(".price").text.replace("$", "")
        ),
        rating=len(product.select_one(".ratings").find_all("span")),
        num_of_reviews=int(
            product.select_one(".review-count").text.split()[0]
        ),
    )
    return product


def get_single_page_products(page_url: str) -> list[Product]:
    driver = webdriver.Edge()
    driver.get(page_url)
    driver.find_element(By.CSS_SELECTOR, ".acceptCookies").click()

    try:
        button = driver.find_element(
            By.CLASS_NAME, "ecomerce-items-scroll-more"
        )
        try:
            while button.is_displayed() and button.is_enabled():
                driver.execute_script(
                    "arguments[0].scrollIntoView(true);", button
                )
                time.sleep(1)
                button.click()
        except ElementNotInteractableException:
            pass
    except NoSuchElementException:
        pass

    html = driver.page_source
    driver.quit()

    soup = BeautifulSoup(html, "html.parser")
    products = soup.select(".card-body")
    return [parse_single_product(product) for product in products]


def write_products_to_csv(filename: str, products: list[Product]) -> None:
    with open(f"{filename}.csv", "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(PRODUCT_FIELDS)
        writer.writerows([astuple(product) for product in products])


def get_all_products() -> None:
    for name, url in URLS.items():
        write_products_to_csv(name, get_single_page_products(url))


if __name__ == "__main__":
    get_all_products()
