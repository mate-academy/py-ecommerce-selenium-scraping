from dataclasses import dataclass
from urllib.parse import urljoin
import csv

from selenium import webdriver
from selenium.common import ElementNotInteractableException, TimeoutException
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec

BASE_URL = "https://webscraper.io/test-sites/e-commerce/more/"


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


class Driver:
    _instance = None

    def __new__(cls, *args, **kwargs) -> "Driver":
        if cls._instance is None:
            cls._instance = super().__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self) -> None:
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        self.driver = webdriver.Chrome(options=options)

    def get_driver(self) -> WebDriver:
        return self.driver


_driver = Driver().get_driver()

pages = [
    {"name": "home", "url": BASE_URL},
    {"name": "computers", "url": urljoin(BASE_URL, "computers")},
    {"name": "laptops", "url": urljoin(BASE_URL, "computers/laptops")},
    {"name": "tablets", "url": urljoin(BASE_URL, "computers/tablets")},
    {"name": "phones", "url": urljoin(BASE_URL, "phones")},
    {"name": "touch", "url": urljoin(BASE_URL, "phones/touch")}
]


def parse_single_product(product_card: WebElement) -> Product:
    title = product_card.find_element(By.CLASS_NAME,
                                      "title").get_attribute("title")
    description = product_card.find_element(By.CLASS_NAME, "description").text
    price = float(product_card.find_element(By.CLASS_NAME, "price").text[1:])
    stars = product_card.find_elements(By.CLASS_NAME, "ws-icon-star")
    rating = len(stars)
    reviews_string = product_card.find_element(By.CLASS_NAME, "ratings").text
    num_of_reviews = int(reviews_string.split(" ")[0])

    return Product(
        title=title,
        description=description,
        price=price,
        rating=rating,
        num_of_reviews=num_of_reviews
    )


def parse_page(url: str) -> list[Product]:
    _driver.get(url)

    try:
        WebDriverWait(_driver, 5).until(
            ec.element_to_be_clickable((By.CLASS_NAME, "acceptCookies"))
        ).click()
    except (TimeoutException, ElementNotInteractableException):
        pass

    products = []

    while True:
        try:
            WebDriverWait(_driver, 5).until(
                ec.element_to_be_clickable(
                    (By.CLASS_NAME, "ecomerce-items-scroll-more"))
            ).click()
        except (TimeoutException, ElementNotInteractableException):
            break

    product_cards = _driver.find_elements(By.CLASS_NAME, "thumbnail")

    for card in product_cards:
        products.append(parse_single_product(card))

    return products


def write_products_to_the_file(
        products: list[Product], file_name: str) -> None:
    with open(file_name, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["title", "description", "price",
                         "rating", "num_of_reviews"])

        for product in products:
            writer.writerow([product.title,
                             product.description,
                             product.price,
                             product.rating,
                             product.num_of_reviews])


def get_all_products() -> None:
    for page in pages:
        products = parse_page(page["url"])
        write_products_to_the_file(products, f"{page['name']}.csv")

    _driver.quit()


if __name__ == "__main__":
    get_all_products()
