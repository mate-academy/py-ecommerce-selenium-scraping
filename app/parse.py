import time
import csv
from urllib.parse import urljoin
from dataclasses import dataclass, fields, astuple
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.ie.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement


BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")
COMPUTERS_URL = urljoin(HOME_URL, "computers/")
PHONES_URL = urljoin(HOME_URL, "phones/")
LAPTOPS_URL = urljoin(COMPUTERS_URL, "laptops")
TABLETS_URL = urljoin(COMPUTERS_URL, "tablets")
TOUCH_URL = urljoin(PHONES_URL, "touch")


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


PRODUCT_FIELDS = [field.name for field in fields(Product)]


def scroll_page(driver: WebDriver) -> None:
    while True:
        try:
            button = driver.find_element(
                By.CLASS_NAME,
                "ecomerce-items-scroll-more"
            )
            driver.execute_script(
                "arguments[0].scrollIntoView(true);",
                button
            )
            button.click()
            time.sleep(1)
        except Exception:
            break


def parse_single_product(product: WebElement) -> Product:
    title = product.find_element(By.CLASS_NAME, "title").get_property("title")
    description = product.find_element(By.CLASS_NAME, "description").text
    price = float(product.find_element(
        By.CLASS_NAME,
        "price"
    ).text.replace("$", ""))
    rating = len(product.find_elements(By.CLASS_NAME, "ws-icon-star"))
    num_of_reviews = int(product.find_element(
        By.CLASS_NAME,
        "review-count"
    ).text.strip().split()[0])
    return Product(
        title=title,
        description=description,
        price=price,
        rating=rating,
        num_of_reviews=num_of_reviews
    )


def get_products(url: str, with_scroll: bool = False) -> [Product]:
    with webdriver.Chrome() as driver:
        driver.get(url)
        if with_scroll:
            scroll_page(driver)
        products = [
            parse_single_product(product)
            for product in driver.find_elements(By.CLASS_NAME, "card-body")
        ]

    return products


def write_to_file(path: str, products: [Product]) -> None:
    with open(path, "w") as file:
        writer = csv.writer(file)
        writer.writerow(PRODUCT_FIELDS)
        writer.writerows([astuple(product) for product in products])


def get_all_products() -> None:
    laptops = get_products(LAPTOPS_URL, True)
    tablets = get_products(TABLETS_URL, True)
    touch = get_products(TOUCH_URL, True)
    home_products = get_products(HOME_URL, False)
    computers = get_products(COMPUTERS_URL, False)
    phones = get_products(PHONES_URL, False)

    write_to_file("laptops.csv", laptops)
    write_to_file("tablets.csv", tablets)
    write_to_file("touch.csv", touch)
    write_to_file("home.csv", home_products)
    write_to_file("computers.csv", computers)
    write_to_file("phones.csv", phones)


if __name__ == "__main__":
    get_all_products()
