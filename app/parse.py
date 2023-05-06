import csv
import time
from dataclasses import dataclass, fields, astuple
from urllib.parse import urljoin

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.remote.webdriver import WebDriver

from tqdm import tqdm


BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


PRODUCT_FIELDS = [field.name for field in fields(Product)]


PAGES_TO_PARSE = [
    ("home", ""),
    ("computers", "computers"),
    ("laptops", "computers/laptops"),
    ("tablets", "computer/tablets"),
    ("phones", "phones"),
    ("touch", "phones/touch"),
]


def parse_single_product(element: WebElement) -> Product:
    ratings = element.find_element(By.CLASS_NAME, "ratings")
    return Product(
        title=(
            element.find_element(By.CLASS_NAME, "title").get_attribute("title")
        ),
        description=element.find_element(By.CLASS_NAME, "description").text,
        price=float(
            element.find_element(By.CLASS_NAME, "price").text.replace("$", "")
        ),
        rating=len(ratings.find_elements(By.CLASS_NAME, "glyphicon-star")),
        num_of_reviews=int(
            ratings.find_element(By.CLASS_NAME, "pull-right").text.split()[0]
        )
    )


def parse_single_page(driver: WebDriver, page_url: str) -> list[Product]:
    full_url = urljoin(HOME_URL, page_url)
    driver.get(full_url)
    cookies = driver.find_elements(By.CLASS_NAME, "acceptCookies")
    if cookies:
        cookies[0].click()
    buttons = driver.find_elements(By.CLASS_NAME, "ecomerce-items-scroll-more")
    if buttons:
        button = buttons[0]
        while button.is_displayed():
            button.click()
            time.sleep(0.1)
    products = tqdm(
        driver.find_elements(By.CLASS_NAME, "thumbnail"),
        ascii=True,
        desc=f"scraping elements from {page_url if page_url else 'home'}"
    )
    return [parse_single_product(product) for product in products]


def write_products_csv(filename: str, products: list[Product]) -> None:
    with open(f"{filename}.csv", "w") as file:
        writer = csv.writer(file)
        writer.writerow(PRODUCT_FIELDS)
        writer.writerows((astuple(product) for product in products))


def get_all_products() -> None:
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    with webdriver.Chrome(options=options) as new_driver:
        for pagename, page_url in PAGES_TO_PARSE:
            products = parse_single_page(new_driver, page_url)
            write_products_csv(pagename, products)


if __name__ == "__main__":
    get_all_products()
