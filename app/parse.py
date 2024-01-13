import csv
import time
from dataclasses import dataclass, fields, astuple
from urllib.parse import urljoin

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement

BASE_URL = "https://webscraper.io/"

PATHS = {
    "home.csv": "test-sites/e-commerce/more/",
    "computers.csv": "test-sites/e-commerce/more/computers/",
    "phones.csv": "test-sites/e-commerce/more/phones/",
    "tablets.csv": "test-sites/e-commerce/more/computers/tablets",
    "touch.csv": "test-sites/e-commerce/more/phones/touch",
    "laptops.csv": "test-sites/e-commerce/more/computers/laptops",
}


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


PRODUCT_FIELDS = [field.name for field in fields(Product)]


def parse_product(product: WebElement) -> Product:
    title = product.find_element(By.CLASS_NAME, "title").get_attribute("title")
    description = product.find_element(By.CLASS_NAME, "description").text
    price = float(
        product.find_element(By.CLASS_NAME, "price").text.replace("$", "")
    )
    rating = len(product.find_elements(By.CLASS_NAME, "glyphicon-star"))
    num_of_reviews = int(
        product.find_element(
            By.CSS_SELECTOR, "div.ratings > p.pull-right"
        ).text.split()[0]
    )

    return Product(title, description, price, rating, num_of_reviews)


def get_products(driver: webdriver, url: str) -> list[Product]:
    driver.get(urljoin(BASE_URL, url))
    accept_cookies(driver)
    click_more(driver)

    products = []
    product_elements = driver.find_elements(By.CLASS_NAME, "thumbnail")

    for product_element in product_elements:
        product = parse_product(product_element)
        products.append(product)

    return products


def click_more(driver: webdriver) -> None:
    while True:
        try:
            time.sleep(0.1)
            driver.find_element(By.LINK_TEXT, "More").click()
        except NoSuchElementException:
            break


def accept_cookies(driver: webdriver) -> None:
    try:
        driver.find_element(By.CLASS_NAME, "acceptCookies").click()
    except NoSuchElementException:
        pass


def write_to_csv(filename: str, products: list[Product]) -> None:
    with open(filename, "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(PRODUCT_FIELDS)
        writer.writerows([astuple(product) for product in products])


def get_all_products() -> None:
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    driver = webdriver.Chrome(options=options)
    driver.implicitly_wait(1)

    for filename, url in PATHS.items():
        scraped_products = get_products(driver, url)
        write_to_csv(filename, scraped_products)

    driver.quit()


if __name__ == "__main__":
    get_all_products()
