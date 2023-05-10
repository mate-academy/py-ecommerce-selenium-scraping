import csv
from time import sleep
from selenium import webdriver
from dataclasses import dataclass
from urllib.parse import urljoin

from selenium.common import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.remote.webelement import WebElement

HOME_URL = "https://webscraper.io/test-sites/e-commerce/more/"
URLS = [
    [HOME_URL, "home"],
    [urljoin(HOME_URL, "computers"), "computers"],
    [urljoin(HOME_URL, "computers/laptops"), "laptops"],
    [urljoin(HOME_URL, "computers/tablets"), "tablets"],
    [urljoin(HOME_URL, "phones/"), "phones"],
    [urljoin(HOME_URL, "phones/touch"), "touch"],
]
MORE = "ecomerce-items-scroll-more"


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


def initialize_driver() -> webdriver:
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    return webdriver.Chrome(
        executable_path="path/to/chromedriver", options=chrome_options
    )


def load_page(driver: webdriver, url: str) -> webdriver:
    driver.get(url)
    try:
        driver.find_element(By.CLASS_NAME, "acceptCookies").click()
    except NoSuchElementException:
        pass
    return driver


def get_all_data(driver: webdriver, url: str) -> webdriver:
    driver = load_page(driver, url)
    try:
        more_button = driver.find_element(By.CLASS_NAME, MORE)
    except NoSuchElementException:
        more_button = None

    if more_button:
        while more_button.is_displayed():
            more_button.click()
            sleep(0.3)

    return driver


def get_single_product(product: WebElement) -> Product:
    return Product(
        title=product.find_element(By.CLASS_NAME, "title").get_attribute(
            "title"
        ),
        description=product.find_element(By.CLASS_NAME, "description").text,
        price=float(product.find_element(By.CLASS_NAME, "price").text[1:]),
        rating=len(product.find_elements(By.CLASS_NAME, "glyphicon-star")),
        num_of_reviews=int(
            product.find_element(By.CLASS_NAME, "ratings").text.split()[0]
        ),
    )


def get_products_from_page(page: webdriver) -> list[Product]:
    products = page.find_elements(By.CLASS_NAME, "thumbnail")
    return [get_single_product(product) for product in products]


def write_products_to_csv(path: str, products: list[Product]) -> None:
    with open(path, "w") as file:
        csv_writer = csv.writer(file, lineterminator="\n")
        csv_writer.writerow(
            ["title", "description", "price", "rating", "num_of_reviews"]
        )
        for product in products:
            csv_writer.writerow(tuple(product.__dict__.values()))


def get_all_products() -> None:
    driver = initialize_driver()
    with driver:
        for url, name in URLS:
            page = get_all_data(driver, url)
            products = get_products_from_page(page)
            write_products_to_csv(f"{name}.csv", products)


if __name__ == "__main__":
    get_all_products()
