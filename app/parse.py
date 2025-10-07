import csv
import time
from dataclasses import dataclass, astuple, fields
from typing import List

from urllib.parse import urljoin
from selenium import webdriver

from selenium.common import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")
COMPUTER_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/computers")
LAPTOPS_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/computers/laptops")
TABLETS_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/computers/tablets")
PHONES_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/phones")
TOUCH_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/phones/touch")


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


PRODUCT_NAME = [field.name for field in fields(Product)]


def get_driver() -> webdriver:
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")

    driver = webdriver.Chrome(options=options)
    return driver


def cookies(driver: webdriver) -> None:
    try:
        wait = WebDriverWait(driver, 15)
        accept_cookie = wait.until(
            EC.element_to_be_clickable((
                By.CLASS_NAME, "acceptCookies"
            ))
        )

        accept_cookie.click()
        wait.until(
            EC.invisibility_of_element_located((By.CLASS_NAME, "acceptCookies"))
        )
    except TimeoutException:
        print("cookie doesn't found")


def scroll_more(driver: webdriver) -> None:
    while True:
        try:
            wait = WebDriverWait(driver, timeout=15)
            more = wait.until(
                EC.element_to_be_clickable(
                    (
                        By.CLASS_NAME, "ecomerce-items-scroll-more")
                )
            )
            more.click()

        except Exception:
            break


def get_one_product(driver: webdriver) -> list[Product]:
    elements = driver.find_elements(By.CLASS_NAME, "thumbnail")
    arr = []
    for element in elements:
        title = element.find_element(
            By.CLASS_NAME, "title"
        ).get_attribute("title")
        description = element.find_element(By.CLASS_NAME, "description").text
        price = float(
            element.find_element(By.CLASS_NAME, "price")
            .text.replace("$", "")
            .strip()
        )
        rating = len(element.find_elements(By.CLASS_NAME, "ws-icon-star"))
        num_of_reviews = int(
            element.find_element(By.CLASS_NAME, "review-count")
            .text.split(" ")[0]
        )
        arr.append(
            Product(
                title=title,
                description=description,
                price=price,
                rating=rating,
                num_of_reviews=num_of_reviews
            )
        )
    return arr


def handle_page(filename: str, url: str) -> None:
    driver = get_driver()
    driver.get(url)
    WebDriverWait(driver, 5).until(
        EC.presence_of_all_elements_located((By.CLASS_NAME, "thumbnail"))
    )
    cookies(driver)
    scroll_more(driver)
    output_info = get_one_product(driver)
    write_products_to_csv(filename, output_info)
    driver.quit()


def write_products_to_csv(filename: str, information: List[Product]) -> None:
    with open(filename, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(PRODUCT_NAME)
        writer.writerows(astuple(item) for item in information)


def get_all_products() -> None:
    pages = [
        ("home.csv", HOME_URL),
        ("computers.csv", urljoin(HOME_URL, "computers")),
        ("laptops.csv", urljoin(HOME_URL, "computers/laptops")),
        ("tablets.csv", urljoin(HOME_URL, "computers/tablets")),
        ("phones.csv", urljoin(HOME_URL, "phones")),
        ("touch.csv", urljoin(HOME_URL, "phones/touch"))
    ]

    for filename, url in pages:
        handle_page(filename, url)


if __name__ == "__main__":
    get_all_products()
