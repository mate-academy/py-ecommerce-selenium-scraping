import csv
import time
from dataclasses import dataclass, fields, astuple
from urllib.parse import urljoin

from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common import (
    ElementClickInterceptedException,
    ElementNotInteractableException,
    NoSuchElementException
)
from selenium.webdriver.common.by import By

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


def parse_single_product(product: BeautifulSoup) -> Product:
    return Product(
        title=product.select_one(".title")["title"],
        description=product.select_one(".description").text.replace(
            "\xa0",
            " "
        ),
        price=float(product.select_one(".price").text[1:]),
        rating=len(product.select(".ws-icon-star")),
        num_of_reviews=int(product.select_one(
            ".ratings .review-count"
        ).text.split()[0]),
    )


def wait_for_clickable(button_click: webdriver) -> None:
    try:
        button_click[0].click()
    except (ElementClickInterceptedException, ElementNotInteractableException):
        time.sleep(0.3)
        wait_for_clickable(button_click)


def get_products(driver: webdriver) -> [Product]:
    time.sleep(0.2)
    all_products = []
    try:
        accept_cookies_button = driver.find_element(
            By.CLASS_NAME,
            "acceptContainer"
        )
        accept_cookies_button.click()
    except (NoSuchElementException, ElementNotInteractableException):
        pass

    time.sleep(1)

    while True:
        button_click = driver.find_elements(
            By.CLASS_NAME,
            "ecomerce-items-scroll-more"
        )

        if len(button_click) != 0:
            time.sleep(1)
            if driver.find_element(
                    By.CSS_SELECTOR, ".ecomerce-items-scroll-more"
            ).get_attribute("style"):
                break

            wait_for_clickable(button_click)
        else:
            break

    time.sleep(1)
    html_content = driver.page_source
    soup = BeautifulSoup(html_content, "html.parser")
    soap_products = soup.select(".thumbnail")

    all_products.extend(
        [
            parse_single_product(parse_product)
            for parse_product in soap_products
        ]
    )
    return all_products


def write_to_csv(output_csv_path: str, products: [Product]) -> None:
    with open(output_csv_path, "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(PRODUCT_FIELDS)
        writer.writerows([astuple(product) for product in products])


def get_all_products() -> None:
    chrome_options = Options()
    chrome_options.add_argument("--headless")

    driver = webdriver.Chrome(options=chrome_options)
    driver.get(urljoin(BASE_URL, HOME_URL))

    home = get_products(driver)
    write_to_csv("home.csv", home)

    driver.find_elements(By.CSS_SELECTOR, "#side-menu > li")[2].click()
    computers = get_products(driver)
    write_to_csv("computers.csv", computers)

    driver.find_elements(By.CLASS_NAME, "subcategory-link")[1].click()
    laptops = get_products(driver)
    write_to_csv("laptops.csv", laptops)
    driver.execute_script("window.scrollTo(0, 0);")
    time.sleep(2)

    driver.find_elements(By.CLASS_NAME, "subcategory-link")[0].click()
    tablets = get_products(driver)
    write_to_csv("tablets.csv", tablets)
    driver.execute_script("window.scrollTo(0, 0);")
    time.sleep(2)

    driver.find_elements(By.CSS_SELECTOR, "#side-menu > li")[1].click()
    phones = get_products(driver)
    write_to_csv("phones.csv", phones)
    time.sleep(2)

    driver.find_elements(By.CLASS_NAME, "subcategory-link")[0].click()
    touch = get_products(driver)
    write_to_csv("touch.csv", touch)
    driver.close()


if __name__ == "__main__":
    get_all_products()
