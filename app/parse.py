import csv

from dataclasses import dataclass
from time import sleep
from urllib.parse import urljoin

from selenium import webdriver
from selenium.common import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.remote.webelement import WebElement


BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")
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


def get_all_data(driver: webdriver, url: str) -> None:
    driver.get(url)
    try:
        driver.find_element(By.CLASS_NAME, "acceptCookies").click()
    except NoSuchElementException:
        pass
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
        title=product.find_element(
            By.CLASS_NAME, "title"
        ).get_attribute("title"),
        description=product.find_element(By.CLASS_NAME, "description").text,
        price=float(product.find_element(By.CLASS_NAME, "price").text[1:]),
        rating=len(product.find_elements(By.CLASS_NAME, "glyphicon-star")),
        num_of_reviews=int(
            product.find_element(By.CLASS_NAME, "ratings").text.split()[0]
        ),
    )


def write_to_csv(path: str, products: list[Product]) -> None:
    with open(path, "w") as file:
        csv_writer = csv.writer(file, lineterminator="\n")
        csv_writer.writerow(
            ["title", "description", "price", "rating", "num_of_reviews"]
        )
        for product in products:
            csv_writer.writerow(tuple(product.__dict__.values()))


def get_all_products() -> None:
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    driver = webdriver.Chrome(
        executable_path="path/to/chromedriver", options=chrome_options
    )

    with driver:
        for url, name in URLS:
            page = get_all_data(driver, url)
            raw_products = page.find_elements(By.CLASS_NAME, "thumbnail")
            products = [
                get_single_product(product) for product in raw_products
            ]
            write_to_csv(f"{name}.csv", products)


if __name__ == "__main__":
    get_all_products()
