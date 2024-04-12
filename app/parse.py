import csv
import time
from dataclasses import dataclass, astuple, fields
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from selenium.webdriver.chrome.options import Options
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")

_driver: WebDriver | None = None


def get_driver() -> WebDriver:
    return _driver


def set_driver(new_driver: WebDriver) -> None:
    global _driver
    _driver = new_driver


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


PRODUCT_FIELDS = [field.name for field in fields(Product)]


def single_product(product: WebElement) -> Product:
    return Product(
        title=product.find_element(
            By.CLASS_NAME, "title"
        ).get_property("title"),
        description=product.find_element(By.CLASS_NAME, "description").text,
        price=float(product.find_element(By.CLASS_NAME, "price").text.replace(
            "$", ""
        )),
        rating=len(product.find_elements(By.CLASS_NAME, "ws-icon-star")),
        num_of_reviews=int(product.find_element(
            By.CLASS_NAME, "review-count"
        ).text.split()[0])
    )


def get_all_urls(base_url: str) -> [str]:
    page = requests.get(base_url).content
    soup_page = BeautifulSoup(page, "html.parser")
    url_soup = soup_page.select(".flex-column > .nav-item")
    urls_list = []
    for url in url_soup:
        url_str = str(url.select_one("a")["href"])
        urls_list.append(url_str)
        if url.select_one(".ws-icon-right "):
            detail_page = urljoin(BASE_URL, url_str)
            detail_page = requests.get(detail_page).content
            soup_detail_page = BeautifulSoup(detail_page, "html.parser")
            urls_detail = soup_detail_page.select(".nav-second-level")
            for url_detail in urls_detail:
                url = url_detail.find_all("a", "subcategory-link")
                urls = [u["href"] for u in url]
                urls_list += urls
    full_urls_list = [urljoin(BASE_URL, url) for url in urls_list]
    return full_urls_list


def get_names_with_urls(url: str) -> [(str, str)]:
    pages = get_all_urls(url)
    names = []
    for page in pages:
        name = page.split("/")[-1]
        if name == "more":
            name = "home"
        names.append(f"{name}.csv")
    names_with_url = list(zip(names, pages))
    return names_with_url


def parse_page(url: str, driver: webdriver) -> [Product]:
    driver.get(url)

    cookies_button = driver.find_elements(By.CLASS_NAME, "acceptCookies")
    if cookies_button:
        cookies_button[0].click()

    scroll_button = driver.find_elements(
        By.CLASS_NAME, "ecomerce-items-scroll-more"
    )
    if scroll_button:
        while scroll_button[0].is_displayed():
            scroll_button[0].click()
            time.sleep(1)

    products = driver.find_elements(By.CLASS_NAME, "card-body")

    result = []
    for product in products:
        result.append(single_product(product))
    return result


def write_to_file(filename: str, products: list[Product]) -> None:
    with open(filename, "w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)

        writer.writerow(PRODUCT_FIELDS)
        writer.writerows([astuple(product) for product in products])


def get_all_products() -> None:
    chrome_options = Options()
    chrome_options.add_argument("headless")
    with webdriver.Chrome(options=chrome_options) as new_driver:
        set_driver(new_driver)
        pages = get_names_with_urls(HOME_URL)
        for name, page in pages:
            all_products = parse_page(page, new_driver)
            write_to_file(name, all_products)


if __name__ == "__main__":
    get_all_products()
