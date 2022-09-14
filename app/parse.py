import csv
import time
from dataclasses import dataclass, fields, astuple
from telnetlib import EC
from urllib.parse import urljoin

import requests
import selenium
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import BaseWebDriver, WebDriver
from selenium.webdriver.support.wait import WebDriverWait

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")
LIST_URLS = [
    (HOME_URL, "home.csv"),
    (urljoin(HOME_URL, "computers"), "computers.csv"),
    (urljoin(HOME_URL, "computers/laptops"), "laptops.csv"),
    (urljoin(HOME_URL, "computers/tablets"), "tablets.csv"),
    (urljoin(HOME_URL, "phones"), "phones.csv"),
    (urljoin(HOME_URL, "phones/touch"), "touch.csv"),
]


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


PRODUCT_FIELDS = [field.name for field in fields(Product)]


class NewWebDriver:
    def __init__(self):
        self.driver = None

    def get_driver(self):
        return self.driver

    def set_driver(self, new_driver):
        self.driver = new_driver

    def close_driver(self):
        return self.driver.close()


def get_single_product(driver) -> Product:
    # return Product(
    #     title=product_soup.select_one(".title")["title"],
    #     description=product_soup.select_one(".description").text,
    #     price=float(product_soup.select_one(".price").text.replace("$", "")),
    #     rating=int(len(product_soup.select(".glyphicon-star"))),
    #     num_of_reviews=int(product_soup.select_one(".ratings > .pull-right").text.split()[0])
    # )
    # return Product(
    #     title=product_soup.select_one(".caption").text.split("\n")[2],
    #     description=product_soup.select_one(".description").text,
    #     price=float(product_soup.select_one(".price").text.replace("$", "")),
    #     rating=int(len(product_soup.select(".glyphicon-star"))),
    #     num_of_reviews=int(product_soup.select_one(".ratings").text.split()[0]),
    # )
    return Product(
        title=driver.find_element(By.CLASS_NAME, "caption").text.split("\n")[1],
        description=driver.find_element(By.CLASS_NAME, "description").text,
        price=driver.find_element(By.CLASS_NAME, "price").text.replace("$", ""),
        rating=int(len(driver.find_elements(By.CLASS_NAME, "glyphicon-star"))),
        num_of_reviews=driver.find_element(By.CLASS_NAME, "ratings").text.split()[0],
    )


# def get_detail_page(product):
#     detail_url = urljoin(BASE_URL, product.find_element(By.CLASS_NAME, "title").get_attribute("href"))
#     # detail_url = urljoin(BASE_URL, product.select_one("title")["href"])
#     page = requests.get(detail_url).content
#     product_soup = BeautifulSoup(page, "html.parser")
#     # detail_url = urljoin(BASE_URL, product.find_element(By.CLASS_NAME, "title").get_attribute("href"))
#     # driver = element.get_driver()
#     # driver.get(detail_url)
#     return get_single_product(product_soup)


def parse_single_page_product(url) -> [Product]:

    # driver = element.get_driver()
    # driver.get(url)
    driver = webdriver.Chrome()
    driver.get(url)

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
            time.sleep(0.2)
    finally:
        # page = requests.get(url).content
        # soup = BeautifulSoup(page, "html.parser")
        products = driver.find_elements(By.CLASS_NAME, "thumbnail")
        # products = soup.select(".thumbnail")
        return [get_single_product(product) for product in products]


def write_products_to_csv(products: [Product], output_csv_path: str) -> None:
    with open(output_csv_path, "w", newline="",) as file:

        writer = csv.writer(file)
        writer.writerow(PRODUCT_FIELDS)
        writer.writerows([astuple(product) for product in products])


def get_all_products():
    # print(parse_single_page_product("https://webscraper.io/test-sites/e-commerce/more/computers/tablets"))
    # dr = NewWebDriver()
    # dr.set_driver(webdriver.Chrome())
    for page in LIST_URLS:
        write_products_to_csv(parse_single_page_product(page[0]), page[1])


if __name__ == "__main__":
    get_all_products()

