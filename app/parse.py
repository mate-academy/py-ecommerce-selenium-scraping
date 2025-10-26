import csv
import time
from dataclasses import dataclass, fields, astuple
from itertools import product
from urllib.parse import urljoin

from bs4 import BeautifulSoup, Tag
from selenium import webdriver
from selenium.common import NoSuchElementException
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")
COMPUTERS_URL = urljoin(HOME_URL, "computers/")
LAPTOPS_URL = urljoin(COMPUTERS_URL, "laptops")
TABLETS_URL = urljoin(COMPUTERS_URL, "tablets")
PHONES_URL = urljoin(HOME_URL, "phones/")
TOUCH_URL = urljoin(PHONES_URL, "touch")

_driver: WebDriver | None = None


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


def get_driver() -> WebDriver:
    return _driver


def set_driver(driver: WebDriver) -> None:
    global _driver
    _driver = driver


PRODUCT_FIELDS = [field.name for field in fields(Product)]


def get_full_content(url: str) -> list[Product]:
    driver = get_driver()
    driver.get(url)
    try:
        cookie = driver.find_element(By.CLASS_NAME, "acceptCookies")
        cookie.click()
    except NoSuchElementException:
        print("No cookie button")
    except Exception as e:
        print(e)
    try:
        while True:
            more = driver.find_element(By.CLASS_NAME, "ecomerce-items-scroll-more")
            time.sleep(1)
            more.click()
            if not more.is_displayed():
                break
    except Exception as e:
        print(e)
    finally:
        products = driver.find_elements(By.CSS_SELECTOR, ".card.thumbnail")
    result = []
    for item in products:
        html = item.get_attribute("outerHTML")  # ← convert WebElement to HTML string
        soup = BeautifulSoup(html, "html.parser")  # ← parse as Tag
        product = parse_single_product(soup)
        result.append(product)
    return result


def parse_single_product(product: Tag) -> Product:
    return Product(
        title=product.select_one(".title")["title"],
        description=product.select_one(".description").text,
        price=float(product.select_one(".price").text.replace("$", "")),
        rating=int(len(product.select(".ws-icon-star"))),
        num_of_reviews=int(product.select_one(".review-count").text.split()[0]),
    )


def write_products_to_csv(products: list[Product], file_name: str) -> None:
    with open(file_name, "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(PRODUCT_FIELDS)
        writer.writerows([astuple(product) for product in products])


def get_all_products() -> None:
    with webdriver.Chrome() as driver:
        set_driver(driver)
        write_products_to_csv(get_full_content(HOME_URL), "home.csv")
        write_products_to_csv(get_full_content(COMPUTERS_URL), "computers.csv")
        write_products_to_csv(get_full_content(LAPTOPS_URL), "laptops.csv")
        write_products_to_csv(get_full_content(TABLETS_URL), "tablets.csv")
        write_products_to_csv(get_full_content(PHONES_URL), "phones.csv")
        write_products_to_csv(get_full_content(TOUCH_URL), "touch.csv")


if __name__ == "__main__":
    get_all_products()
