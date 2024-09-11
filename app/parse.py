import csv
import time
from dataclasses import dataclass, astuple
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common import (
    NoSuchElementException,
    ElementClickInterceptedException
)
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By

BASE_URL = "https://webscraper.io/"


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


_driver: WebDriver | None = None


def get_driver() -> WebDriver:
    return _driver


def set_driver() -> None:
    global _driver
    _driver = webdriver.Chrome()


def close_driver() -> None:
    global _driver
    _driver.close()


def get_list_of_elements(html_page: BeautifulSoup) -> list[Product]:
    all_elements = html_page.select(".card.thumbnail")
    return [
        Product(
            title=element.select_one(".title")["title"],
            description=element.select_one(
                ".description"
            ).text.replace("\xa0", " "),
            price=float(element.select_one(
                ".price"
            ).text.replace("$", "")),
            rating=len(element.select_one(
                ".ratings"
            ).select(".ws-icon.ws-icon-star")),
            num_of_reviews=int(element.select_one(
                ".ratings"
            ).select_one(".review-count").text.split()[0])
        )
        for element in all_elements
    ]


def page_final_page(url_page: str) -> BeautifulSoup:
    url = urljoin(BASE_URL, url_page)
    driver = get_driver()
    driver.get(url)
    try:
        button = driver.find_element(
            By.CSS_SELECTOR,
            ".btn.btn-lg.btn-block.btn-primary.ecomerce-items-scroll-more"
        )
    except NoSuchElementException:
        return BeautifulSoup(driver.page_source, "html.parser")

    while True:
        if "display" in button.get_attribute("style"):
            break
        try:
            button.click()
        except ElementClickInterceptedException:
            cookie = driver.find_element(By.CSS_SELECTOR, ".acceptCookies")
            cookie.click()
        time.sleep(0.1)

    return BeautifulSoup(driver.page_source, "html.parser")


def write_products_to_csv(products: list[Product], name_page: str) -> None:
    with open(f"{name_page}.csv", "w", newline="", encoding="utf-8") as file:
        write = csv.writer(file)
        write.writerow([
            "title",
            "description",
            "price",
            "rating",
            "num_of_reviews"
        ])
        write.writerows([astuple(product) for product in products])


def parse_pages(list_of_all_urls: dict) -> None:
    for page_name in list_of_all_urls:
        full_html_page = page_final_page(list_of_all_urls[page_name])
        print(get_list_of_elements(full_html_page))
        write_products_to_csv(get_list_of_elements(full_html_page), page_name)


def get_all_products() -> None:
    set_driver()
    list_of_all_urls = {
        "home": "test-sites/e-commerce/more/",
        "computers": "test-sites/e-commerce/more/computers",
        "laptops": "test-sites/e-commerce/more/computers/laptops",
        "tablets": "test-sites/e-commerce/more/computers/tablets",
        "phones": "test-sites/e-commerce/more/phones",
        "touch": "test-sites/e-commerce/more/phones/touch"
    }
    parse_pages(list_of_all_urls)
    close_driver()


if __name__ == "__main__":
    get_all_products()
