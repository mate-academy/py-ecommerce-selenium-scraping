import csv
import time
from dataclasses import dataclass, fields, astuple
from urllib.parse import urljoin
from bs4 import BeautifulSoup, Tag
from selenium import webdriver
from selenium.common import NoSuchElementException
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
    "touch": urljoin(HOME_URL, "phones/touch")
}


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


def parse_single_product(product: Tag) -> Product:
    return Product(
        title=product.select_one(".caption > h4:nth-of-type(2)").text,
        description=product.select_one(".description").text,
        price=float(product.select_one(".caption > h4").text.replace("$", "")),
        rating=len(product.select(".glyphicon")),
        num_of_reviews=int(product.select_one(".ratings > p").text.split()[0])
    )

def press_more_buttun(url: str, driver: WebDriver) -> list[Product]:
    driver.get(url)
    scroll_button = None

    try:
        driver.find_element(By.CLASS_NAME, "acceptCookies").click()
    except NoSuchElementException:
        pass

    try:
        scroll_button = driver.find_element(
            By.CLASS_NAME, "ecomerce-items-scroll-more"
        )
    except NoSuchElementException:
        pass

    if scroll_button is not None:
        while scroll_button.is_displayed():
            scroll_button.click()
            time.sleep(0.5)

    page = driver.page_source
    soup = BeautifulSoup(page, "html.parser")
    products = soup.select(".thumbnail")
    return [
        parse_single_product(product)
        for product in products
    ]


def csv_data_file_create(file_name: str, products: list[Product]) -> None:
    with open(file_name, "w") as file:
        csv_file = csv.writer(file)
        csv_file.writerow([field.name for field in fields(Product)])
        csv_file.writerows([astuple(quote) for quote in products])


def get_all_products() -> None:
    options = Options()
    options.add_argument("--headless")

    with webdriver.Chrome(options=options) as driver:
        for name, url in URLS.items():
            products = press_more_buttun(url, driver)
            csv_data_file_create(f"{name}.csv", products)


if __name__ == "__main__":
    get_all_products()
