import csv
import time

from dataclasses import dataclass, astuple
from urllib.parse import urljoin

from selenium import webdriver
from selenium.common import NoSuchElementException
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more")
COMPUTERS_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/computers")
PHONES_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/phones")
LAPTOPS_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/computers/laptops")
TABLETS_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/computers/tablets")
TOUCH_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/phones/touch")


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


def get_products_from_page(driver: WebDriver, url: str) -> list[Product]:
    driver.get(url)
    time.sleep(1)
    driver.refresh()
    while True:
        try:
            button = driver.find_element(By.CLASS_NAME, "ecomerce-items-scroll-more")
        except NoSuchElementException:
            break
        if button.get_attribute("style") == "display: none;":
            break
        button.click()
        time.sleep(1)
    products_soup = driver.find_elements(By.CLASS_NAME, "product-wrapper")
    products = []
    for product_soup in products_soup:
        products.append(
            Product(
                title=product_soup.find_element(By.CLASS_NAME, "title").get_attribute("title"),
                description=product_soup.find_element(By.CLASS_NAME, "description").text,
                price=float(product_soup.find_element(By.CLASS_NAME, "price").text[1:]),
                rating=len(product_soup.find_elements(By.CSS_SELECTOR, ".ratings span")),
                num_of_reviews=int(product_soup.find_element(By.CLASS_NAME, "review-count").text.split()[0]),
            )
        )

    return products


def write_to_csv(products: list[Product], filename: str) -> None:
    with open(filename, "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["title", "description", "price", "rating", "num_of_reviews"])
        writer.writerows([astuple(product) for product in products])


def get_all_products() -> None:
    with webdriver.Chrome() as driver:
        time.sleep(5)
        home_products = get_products_from_page(driver, HOME_URL)
        computers = get_products_from_page(driver, COMPUTERS_URL)
        phones = get_products_from_page(driver, PHONES_URL)
        laptops = get_products_from_page(driver, LAPTOPS_URL)
        tablets = get_products_from_page(driver, TABLETS_URL)
        touch = get_products_from_page(driver, TOUCH_URL)
        write_to_csv(home_products, "home.csv")
        write_to_csv(computers, "computers.csv")
        write_to_csv(phones, "phones.csv")
        write_to_csv(laptops, "laptops.csv")
        write_to_csv(tablets, "tablets.csv")
        write_to_csv(touch, "touch.csv")


if __name__ == "__main__":
    get_all_products()
