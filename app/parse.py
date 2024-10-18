import csv
import time
import requests
from selenium import webdriver
from selenium.common import ElementNotInteractableException
from selenium.webdriver.common.by import By
from dataclasses import dataclass, fields
from urllib.parse import urljoin
from bs4 import BeautifulSoup

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


def parse_single_product(soup: BeautifulSoup) -> Product:
    title = soup.select_one(".title")["title"]
    description = soup.select_one(".description").text.replace("\xa0", " ")
    price = soup.select_one(".price").text.replace("$", "")
    rating = soup.select(".ws-icon")
    num_of_reviews = soup.select_one(".ratings > .review-count").text
    return Product(
        title=title,
        description=description,
        price=float(price),
        rating=len(rating),
        num_of_reviews=int(num_of_reviews.split()[0])
    )


def get_product_with_pagination_button(url: str) -> [Product]:
    option = webdriver.ChromeOptions()
    option.add_argument("headless")
    driver = webdriver.Chrome(options=option)
    driver.get(url)
    while True:
        try:
            button_more = driver.find_element(
                By.CLASS_NAME,
                "ecomerce-items-scroll-more"
            )
            button_more.click()
            time.sleep(1)
        except ElementNotInteractableException:
            break

    page = driver.page_source
    driver.close()
    soup = BeautifulSoup(page, "html.parser")
    products = soup.select(".product-wrapper")
    return [parse_single_product(product) for product in products]


def get_products_from_every_page(url: str) -> [Product]:
    page = requests.get(url).content
    soup = BeautifulSoup(page, "html.parser")
    button_element = soup.select_one(".ecomerce-items-scroll-more")

    if not button_element:
        products = soup.select(".product-wrapper")
        return [parse_single_product(product) for product in products]
    return get_product_with_pagination_button(url)


def write_products(output_csv_path: str, products: list[Product]) -> None:
    with open(output_csv_path, "w", newline="", encoding="utf8") as file:
        writer = csv.writer(file)
        writer.writerow([field.name for field in fields(Product)])
        for product in products:
            writer.writerow(
                [
                    product.title,
                    product.description,
                    product.price,
                    product.rating,
                    product.num_of_reviews
                ]
            )


def get_all_products() -> None:
    pages = {
        "home": HOME_URL,
        "computers": COMPUTERS_URL,
        "laptops": LAPTOPS_URL,
        "tablets": TABLETS_URL,
        "phones": PHONES_URL,
        "touch": TOUCH_URL

    }
    csv_files = {
        "home": "home.csv",
        "computers": "computers.csv",
        "laptops": "laptops.csv",
        "tablets": "tablets.csv",
        "phones": "phones.csv",
        "touch": "touch.csv"

    }
    for page, url in pages.items():
        products = get_products_from_every_page(url)
        write_products(csv_files[page], products)


if __name__ == "__main__":
    get_all_products()
