import csv
import time
from dataclasses import dataclass, fields, astuple
from urllib.parse import urljoin

from bs4 import Tag, BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")

COMPUTERS_URL = urljoin(HOME_URL, "computers/")
LAPTOPS_URL = urljoin(COMPUTERS_URL, "laptops")
TABLETS_URL = urljoin(COMPUTERS_URL, "tablets")

PHONES_URL = urljoin(HOME_URL, "phones/")
TOUCH_URL = urljoin(PHONES_URL, "touch")


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


PRODUCT_FIELDS = [field.name for field in fields(Product)]


def parse_single_product(product: Tag) -> Product:
    return Product(
        title=product.select_one(".title").get("title"),
        description=product.select_one(".description").text,
        price=float(product.select_one(".price").text.replace("$", "")),
        rating=len(product.select_one(".ratings p:not(.review-count)").select("span")),
        num_of_reviews=int(product.select_one(".review-count").text.split()[0]),
    )


def get_page_products(driver: webdriver.Chrome, url: str) -> list[Product]:
    driver.get(url)
    try:
        WebDriverWait(driver, 10).until(
            ec.presence_of_element_located((By.CSS_SELECTOR, ".card-body"))
        )
    except TimeoutException:
        return []
    try:
        accept_button = WebDriverWait(driver, 3).until(
            ec.element_to_be_clickable((By.CSS_SELECTOR, "button[data-tid='banner-accept']"))
        )
        accept_button.click()
        time.sleep(0.3)
    except TimeoutException:
        pass
    while True:
        cards_before = len(driver.find_elements(By.CSS_SELECTOR, ".card-body"))
        try:
            more = WebDriverWait(driver, 2).until(
                ec.presence_of_element_located((By.CSS_SELECTOR, ".ecomerce-items-scroll-more"))
            )
        except TimeoutException:
            break
        if not more.is_displayed():
            break
        try:
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", more)
            more.click()
        except ElementClickInterceptedException:
            driver.execute_script("arguments[0].click();", more)
        time.sleep(0.5)
        cards_after = len(driver.find_elements(By.CSS_SELECTOR, ".card-body"))
        if cards_after == cards_before:
            break
    soup = BeautifulSoup(driver.page_source, "html.parser")
    products = soup.select(".card-body")
    return [parse_single_product(product) for product in products]


def write_products_to_csv(file_name: str, products: list[Product]) -> None:
    with open(file_name, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(PRODUCT_FIELDS)
        writer.writerows([astuple(product) for product in products])


def get_all_products() -> None:
    file_names_url = {
        "home.csv": HOME_URL,
        "computers.csv": COMPUTERS_URL,
        "laptops.csv": LAPTOPS_URL,
        "tablets.csv": TABLETS_URL,
        "phones.csv": PHONES_URL,
        "touch.csv": TOUCH_URL,
    }

    options = webdriver.ChromeOptions()

    with webdriver.Chrome(options=options) as driver:
        for file_name, url in file_names_url.items():
            products = get_page_products(driver, url)
            write_products_to_csv(file_name, products)


if __name__ == "__main__":
    get_all_products()
