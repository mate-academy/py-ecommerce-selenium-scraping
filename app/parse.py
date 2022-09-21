import csv
import time

from dataclasses import dataclass
from urllib.parse import urljoin

from selenium.common import NoSuchElementException
from selenium.webdriver.chrome.service import Service
from selenium import webdriver
from selenium.webdriver.common.by import By

s = Service("C:/Users/Anton/chrome_driver_for_selenium/chromedriver.exe")
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


def create_file(data: list, file_name: str):

    with open(file_name, "w", encoding='utf-8', newline="") as file:
        first_row = ["title", "description", "price", "rating", "num_of_reviews"]

        writer = csv.writer(file)
        writer.writerow(first_row)
        writer.writerows(data)


def parce_single_page(link: str, file_name: str):
    driver = webdriver.Chrome(service=s)
    driver.get(link)
    products_info = []
    cookies = driver.find_element(By.CLASS_NAME, "acceptCookies")
    if cookies.is_displayed():
        cookies.click()
    try:
        button_more = driver.find_element(By.CLASS_NAME, "ecomerce-items-scroll-more")
    except NoSuchElementException:
        pass
    else:
        while button_more.is_displayed():
            button_more.click()
            time.sleep(0.5)
    finally:
        products = driver.find_elements(By.CSS_SELECTOR, "div.col-sm-4")

        for product in products:
            title = product.find_element(By.CLASS_NAME, "title").get_attribute("title")
            description = product.find_element(By.CLASS_NAME, "description").text
            price = float(product.find_element(By.CLASS_NAME, "price").text.replace("$", ""))
            rating = int(len(product.find_elements(By.CLASS_NAME, "glyphicon-star")))
            num_of_reviews = int(product.find_element(By.CSS_SELECTOR, ".ratings .pull-right").text.split()[0])

            product_data = [title, description, price, rating, num_of_reviews]

            products_info.append(product_data)

        driver.close()
        create_file(products_info, file_name)


def get_all_products():
    links = [
        (HOME_URL, "home.csv"),
        (COMPUTERS_URL, "computers.csv"),
        (LAPTOPS_URL, "laptops.csv"),
        (TABLETS_URL, "tablets.csv"),
        (PHONES_URL, "phones.csv"),
        (TOUCH_URL, "touch.csv"),
    ]
    for link in links:
        parce_single_page(link[0], link[1])


if __name__ == "__main__":
    get_all_products()
