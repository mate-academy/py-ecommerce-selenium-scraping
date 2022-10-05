import csv
import time
from dataclasses import dataclass
from urllib.parse import urljoin

import selenium.common.exceptions
from selenium import webdriver
from selenium.webdriver.common.by import By

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")
COMPUTERS_URL = urljoin(HOME_URL, "computers/")
LAPTOPS_URL = urljoin(COMPUTERS_URL, "laptops")
TABLETS_URL = urljoin(COMPUTERS_URL, "tablets")
PHONES_URL = urljoin(HOME_URL, "phones/")
TOUCH_URL = urljoin(PHONES_URL, "touch")


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


def driver_open():
    driver = webdriver.Chrome()
    return driver


def driver_close(driver):
    driver.close()


def create_file_for_page(data: list, file_name: str):

    with open(file_name, "w", encoding='utf-8', newline="") as csv_file:
        first_row = ["title", "description", "price", "rating", "num_of_reviews"]

        writer = csv.writer(csv_file)
        writer.writerow(first_row)
        writer.writerows(data)


def parce_single_page(link: str, file_name: str):
    print(link)

    driver = driver_open()
    driver.get(link)
    cookies = driver.find_element(By.CLASS_NAME, "acceptCookies")
    if cookies.is_displayed():
        cookies.click()
    try:
        more_button = driver.find_element(By.CLASS_NAME, "ecomerce-items-scroll-more")
    except selenium.common.exceptions.NoSuchElementException:
        pass
    else:
        while more_button.is_displayed():
            more_button.click()
            time.sleep(0.1)
    finally:

        products = driver.find_elements(By.CSS_SELECTOR, "div.col-sm-4")
        products_data = []

        for product in products:
            title = product.find_element(By.CLASS_NAME, "title").get_attribute("title")
            description = product.find_element(By.CSS_SELECTOR, ".description").text
            price = float(product.find_element(By.CLASS_NAME, "price").text.replace("$", ""))
            rating = int(len(product.find_elements(By.CLASS_NAME, "glyphicon-star")))
            num_of_reviews = int(product.find_element(By.CSS_SELECTOR, ".ratings .pull-right").text.split()[0])

            product_data = [title, description, price, rating, num_of_reviews]

            products_data.append(product_data)

        driver_close(driver)
        create_file_for_page(products_data, file_name)


def list_of_pages_for_parce(links: list[tuple]):

    for link in links:
        parce_single_page(link[0], link[1])


def get_all_products():
    links = [
        (HOME_URL, "home.csv"),
        (COMPUTERS_URL, "computers.csv"),
        (LAPTOPS_URL, "laptops.csv"),
        (TABLETS_URL, "tablets.csv"),
        (PHONES_URL, "phones.csv"),
        (TOUCH_URL, "touch.csv"),
    ]

    list_of_pages_for_parce(links)


if __name__ == "__main__":
    get_all_products()