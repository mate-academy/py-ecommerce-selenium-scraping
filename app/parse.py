import csv
import dataclasses
import time
from dataclasses import dataclass
from urllib.parse import urljoin
from selenium import webdriver
from selenium.common import NoSuchElementException, ElementNotInteractableException, ElementClickInterceptedException
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement


BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")
COMPUTERS_URL = urljoin(HOME_URL, "computers/")
LAPTOPS_URL = urljoin(COMPUTERS_URL, "laptops")
TABLETS_URL = urljoin(COMPUTERS_URL, "tablets")
PHONES_URL = urljoin(HOME_URL, "phones/")
TOUCH_URL = urljoin(PHONES_URL, "touch")

_driver: WebDriver | None = None


def get_driver() -> WebDriver:
    return _driver


def set_driver(new_driver: WebDriver) -> None:
    global _driver
    _driver = new_driver


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


PRODUCT_FIELDS = [field.name for field in dataclasses.fields(Product)]


def parse_single_product(product: WebElement) -> Product:
    title = product.find_element(
        By.CSS_SELECTOR, ".title").get_attribute("title")
    description = product.find_element(
        By.CSS_SELECTOR, ".description").text
    price = float(product.find_element(
        By.CSS_SELECTOR, ".price").text.replace("$", ""))
    rating = len(product.find_elements(
        By.CSS_SELECTOR, ".ratings span.ws-icon-star"))
    num_of_reviews = int(product.find_element(
        By.CSS_SELECTOR, ".review-count").text.split()[0])

    return Product(
        title=title,
        description=description,
        price=price,
        rating=rating,
        num_of_reviews=num_of_reviews
    )


def get_page_products(page_url: str) -> [Product]:
    driver = get_driver()
    driver.get(page_url)

    if cookies := driver.find_elements(By.CLASS_NAME,
                                       "acceptCookies"):
        cookies[0].click()

    while True:
        try:
            driver.find_element(By.CLASS_NAME, "ecomerce-items-scroll-more").click()
            time.sleep(0.2)
        except (
            NoSuchElementException,
            ElementNotInteractableException,
            ElementClickInterceptedException,
        ):
            break

    products = driver.find_elements(By.CLASS_NAME, "card-body")
    return [parse_single_product(product) for product in products]


def write_products_to_csv(products: [Product], file_name: str) -> None:
    with open(file_name, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(PRODUCT_FIELDS)
        writer.writerows(
            [dataclasses.astuple(product) for product in products]
        )


def get_all_products() -> None:
    with webdriver.Chrome() as driver:
        set_driver(driver)
        write_products_to_csv(get_page_products(HOME_URL), "home.csv")
        write_products_to_csv(get_page_products(
            COMPUTERS_URL), "computers.csv"
        )
        write_products_to_csv(get_page_products(LAPTOPS_URL), "laptops.csv")
        write_products_to_csv(get_page_products(TABLETS_URL), "tablets.csv")
        write_products_to_csv(get_page_products(PHONES_URL), "phones.csv")
        write_products_to_csv(get_page_products(TOUCH_URL), "touch.csv")


if __name__ == "__main__":
    get_all_products()
