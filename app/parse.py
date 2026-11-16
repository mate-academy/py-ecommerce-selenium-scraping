import csv
from dataclasses import dataclass, fields, astuple
from urllib.parse import urljoin

import time
from selenium import webdriver
import requests
from bs4 import BeautifulSoup
from selenium.common import (ElementNotInteractableException,
                             ElementClickInterceptedException)
from selenium.webdriver.common.by import By

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")
COMPUTERS_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/computers")


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


FIELDS_NAME = [field.name for field in fields(Product)]


def get_home_page() -> list:
    response = requests.get(HOME_URL).content
    soup = BeautifulSoup(response, "html.parser")
    pages = soup.select(".col-md-4")
    result = []
    for page in pages:
        result.append(
            Product(
                title=page.select_one(".title")["title"],
                description=page.select_one(
                    ".description"
                ).text.replace("\xa0", " "),
                price=float(page.select_one(
                    'span[itemprop="price"]'
                ).text.replace("$", "")),
                rating=int(page.select_one("p[data-rating]")["data-rating"]),
                num_of_reviews=int(page.select_one(
                    'span[itemprop="reviewCount"]'
                ).text)
            )
        )
    return result


def get_computers_page() -> list:
    response = requests.get(COMPUTERS_URL).content
    soup = BeautifulSoup(response, "html.parser")
    pages = soup.select(".col-md-4")
    result = []
    for page in pages:
        result.append(
            Product(
                title=page.select_one(".title")["title"],
                description=page.select_one(
                    ".description"
                ).text.replace("\xa0", " "),
                price=float(page.select_one(
                    'span[itemprop="price"]'
                ).text.replace("$", "")),
                rating=int(page.select_one(
                    "p[data-rating]"
                )["data-rating"]),
                num_of_reviews=int(page.select_one(
                    'span[itemprop="reviewCount"]'
                ).text)
            )
        )
    return result


def get_laptops_page() -> list:
    url = urljoin(BASE_URL, "test-sites/e-commerce/more/computers/laptops")
    driver = webdriver.Chrome()
    driver.get(url)
    buttons = driver.find_element(By.CLASS_NAME, "btn-block")
    time.sleep(4)
    cookies = driver.find_element(By.CSS_SELECTOR,
                                  "button[data-tid='banner-accept']")
    cookies.click()
    while not buttons.get_property("style"):
        try:
            buttons.click()
        except ElementNotInteractableException:
            break

    soup = BeautifulSoup(driver.page_source, "html.parser")
    driver.close()

    pages = soup.select(".col-md-4")
    result = []

    for page in pages:
        result.append(
            Product(
                title=page.select_one("a.title")["title"],
                description=page.select_one(
                    ".description"
                ).text.replace("\xa0", " "),
                price=float(page.select_one(".price").text.replace("$", "")),
                rating=len(page.select(".ws-icon")),
                num_of_reviews=int(page.select_one(
                    "span[itemprop='reviewCount']"
                ).text)
            )
        )
    return result


def get_tablet_page() -> list:
    url = urljoin(BASE_URL,
                  "test-sites/e-commerce/more/computers/tablets")
    driver = webdriver.Chrome()
    driver.get(url)
    buttons = driver.find_element(By.CLASS_NAME, "btn-block")
    time.sleep(4)
    cookies = driver.find_element(By.CSS_SELECTOR,
                                  "button[data-tid='banner-accept']")
    cookies.click()

    while not buttons.get_property("style"):
        try:
            buttons.click()
        except (ElementNotInteractableException,
                ElementClickInterceptedException):
            break

    soup = BeautifulSoup(driver.page_source, "html.parser")
    driver.close()

    pages = soup.select(".col-md-4")
    result = []

    for page in pages:
        result.append(
            Product(
                title=page.select_one("a.title")["title"],
                description=page.select_one(
                    ".description"
                ).text.replace("\xa0", " "),
                price=float(page.select_one(".price").text.replace("$", "")),
                rating=len(page.select(".ws-icon")),
                num_of_reviews=int(page.select_one(
                    "span[itemprop='reviewCount']"
                ).text)
            )
        )
    return result


def get_phone_page() -> list:
    url = urljoin(BASE_URL, "test-sites/e-commerce/more/phones")
    response = requests.get(url).content
    soup = BeautifulSoup(response, "html.parser")
    result = []
    pages = soup.select(".col-md-4")

    for page in pages:
        result.append(
            Product(
                title=page.select_one(".title")["title"],
                description=page.select_one(
                    ".description"
                ).text.replace("\xa0", " "),
                price=float(page.select_one(
                    "span[itemprop='price']"
                ).text.replace("$", "")),
                rating=len(page.select(".ws-icon")),
                num_of_reviews=int(page.select_one(
                    "span[itemprop='reviewCount']"
                ).text)
            )
        )

    return result


def get_touch_page() -> list:
    url = urljoin(BASE_URL, "test-sites/e-commerce/more/phones/touch")
    driver = webdriver.Chrome()
    driver.get(url)
    buttons = driver.find_element(By.CLASS_NAME, "btn-block")
    time.sleep(4)
    cookies = driver.find_element(By.CSS_SELECTOR,
                                  "button[data-tid='banner-accept']")
    cookies.click()

    while not buttons.get_property("style"):
        try:
            time.sleep(0.5)
            buttons.click()
        except ElementNotInteractableException:
            break

    soup = BeautifulSoup(driver.page_source, "html.parser")
    driver.close()

    pages = soup.select(".col-md-4")
    result = []

    for page in pages:
        result.append(
            Product(
                title=page.select_one("a.title")["title"],
                description=page.select_one(
                    ".description"
                ).text.replace("\xa0", " "),
                price=float(page.select_one(".price").text.replace("$", "")),
                rating=len(page.select(".ws-icon")),
                num_of_reviews=int(page.select_one(
                    "span[itemprop='reviewCount']"
                ).text)
            )
        )
    return result


def write_in_file() -> None:
    with open("home.csv", "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(FIELDS_NAME)
        result = get_home_page()
        writer.writerows([astuple(i) for i in result])

    with open("computers.csv", "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(FIELDS_NAME)
        result = get_computers_page()
        writer.writerows([astuple(i) for i in result])

    with open("laptops.csv", "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(FIELDS_NAME)
        result = get_laptops_page()
        writer.writerows([astuple(i) for i in result])

    with open("tablets.csv", "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(FIELDS_NAME)
        result = get_tablet_page()
        writer.writerows([astuple(i) for i in result])

    with open("phones.csv", "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(FIELDS_NAME)
        result = get_phone_page()
        writer.writerows([astuple(i) for i in result])

    with open("touch.csv", "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(FIELDS_NAME)
        result = get_touch_page()
        writer.writerows([astuple(i) for i in result])


def get_all_products() -> None:
    write_in_file()


if __name__ == "__main__":
    get_all_products()
