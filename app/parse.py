import csv
from dataclasses import dataclass, astuple, fields
from time import sleep
from urllib.parse import urljoin
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.webdriver import WebDriver

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")
COMPUTERS_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/computers")
LAPTOPS_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/computers/laptops")
TABLETS_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/computers/tablets")
PHONES_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/phones")
TOUCH_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/phones/touch")

ALL_URLS = {
    HOME_URL: "home.csv",
    COMPUTERS_URL: "computers.csv",
    TABLETS_URL: "tablets.csv",
    PHONES_URL: "phones.csv",
    TOUCH_URL: "touch.csv",
    LAPTOPS_URL: "laptops.csv",
}


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


PRODUCT_FIELDS = [field.name for field in fields(Product)]

_driver: WebDriver | None = None


def get_driver() -> WebDriver:
    return _driver


def set_driver(new_driver: WebDriver) -> None:
    global _driver
    _driver = new_driver


def parse_page(url: str):
    driver = get_driver()
    driver.get(url)

    sleep(2)

    if len(driver.find_elements(By.CLASS_NAME, "acceptCookies")):
        cookies = driver.find_element(By.CLASS_NAME, "acceptCookies")
        cookies.click()

    if len(driver.find_elements(By.CLASS_NAME, "ecomerce-items-scroll-more")):
        more_button = driver.find_element(
            By.CLASS_NAME, "ecomerce-items-scroll-more"
        )
        while more_button.is_displayed():
            more_button.click()
            sleep(0.2)

    products = driver.find_elements(By.CLASS_NAME, "thumbnail")
    return products


def get_all_products() -> None:
    with webdriver.Firefox() as new_driver:
        set_driver(new_driver)
        for url, path in ALL_URLS.items():
            products = parse_page(url)
            res = []
            for product in products:
                res.append(get_single_product(product))
            write_products_to_csv(path, res)


def get_single_product(product) -> Product:
    return Product(
        title=product.find_element(By.CLASS_NAME, "title").get_attribute("title"),
        description=product.find_element(By.CLASS_NAME, "description").text,
        price=float(product.find_element(By.CLASS_NAME, "price").text.replace("$", "")),
        rating=len(product.find_elements(By.CLASS_NAME, "glyphicon-star")),
        num_of_reviews=int(product.find_element(
            By.CLASS_NAME, "ratings"
        ).find_element(
            By.TAG_NAME, "p"
        ).text.split(" ")[0]),
    )


def write_products_to_csv(path: str, products: [Product]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(PRODUCT_FIELDS)
        writer.writerows([astuple(product) for product in products])


if __name__ == "__main__":
    get_all_products()
