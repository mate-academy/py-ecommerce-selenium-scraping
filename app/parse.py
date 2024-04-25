import csv
import time

from dataclasses import dataclass, fields, astuple
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")

ALL_URLS = {
    "computers": urljoin(HOME_URL, "computers"),
    "laptops": urljoin(HOME_URL, "computers/laptops"),
    "tablets": urljoin(HOME_URL, "computers/tablets"),
    "phones": urljoin(HOME_URL, "phones"),
    "touch": urljoin(HOME_URL, "phones/touch")
}


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


PRODUCT_FIELDS = [field.name for field in fields(Product)]


def parse_single_product(product_soup):
    return Product(
        title=product_soup.select_one(".title")["title"],
        description=product_soup.select_one("p.description").text.replace("\xa0", " "),
        price=float(product_soup.select_one(".caption > h4").text.replace("$", "")),
        rating=len(product_soup.select(".ratings span")),
        num_of_reviews=int(product_soup.select_one(".ratings > p").text.split()[0])
    )


def write_products_to_csv(products, file_name):
    with open(file_name, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(PRODUCT_FIELDS)
        writer.writerows([astuple(product) for product in products])


def handle_cookies(driver: webdriver.Chrome) -> None:
    try:
        accept_cookies = WebDriverWait(driver, 5).until(
            ec.element_to_be_clickable((By.CLASS_NAME, "acceptCookies"))
        )
        accept_cookies.click()
    except Exception:
        pass


def handle_show_more(driver: webdriver.Chrome) -> None:
    while True:
        try:
            button = driver.find_element(
                    By.CLASS_NAME, "ecomerce-items-scroll-more"
                )
            time.sleep(1)
            button.click()
        except Exception:
            break


def parse_products_from_soup(soup: BeautifulSoup) -> list:
    products = []
    for product in soup.select(".thumbnail"):
        products.append(parse_single_product(product))
    return products


def get_page_soup(driver:webdriver.Chrome, url: str) -> BeautifulSoup:
    driver.get(url)
    handle_cookies(driver)
    handle_show_more(driver)
    return BeautifulSoup(driver.page_source, "html.parser")


def get_all_products() -> None:
    with webdriver.Chrome() as driver:
        for name, link in ALL_URLS.items():
            soup = get_page_soup(driver, link)
            products = parse_products_from_soup(soup=soup)
            write_products_to_csv(products, f"{name}.csv")
        driver.quit()


if __name__ == "__main__":
    get_all_products()
