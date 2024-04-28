import csv
import time
from dataclasses import dataclass, astuple, fields
from typing import List, Tuple
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from selenium.webdriver.chrome.options import Options
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")


@dataclass
class Product:
    name: str
    description: str
    price: float
    rating: int
    review_count: int


def parse_product_data(product: WebElement) -> Product:
    return Product(
        name=product.find_element(
            By.CLASS_NAME, "title"
        ).get_property("title"),
        description=product.find_element(
            By.CLASS_NAME, "description"
        ).text,
        price=float(product.find_element(
            By.CLASS_NAME, "price"
        ).text.replace("$", "")),
        rating=len(product.find_elements(
            By.CLASS_NAME, "ws-icon-star"
        )),
        review_count=int(
            product.find_element(By.CLASS_NAME, "review-count").text.split()[0]
        ),
    )


def extract_all_urls(base_url: str) -> List[str]:
    page_content = requests.get(base_url).content
    soup = BeautifulSoup(page_content, "html.parser")
    urls = [
        str(
            link.get("href")
        ) for link in soup.select(".flex-column > .nav-item a")
    ]
    urls += [
        str(link.get("href")) for link in soup.select(".ws-icon-right")
    ]
    full_urls = [urljoin(BASE_URL, link) for link in urls]

    for url in urls:
        detail_page_content = requests.get(urljoin(BASE_URL, url)).content
        soup_detail_page = BeautifulSoup(detail_page_content, "html.parser")
        detail_page_urls = soup_detail_page.select(
            ".nav-second-level a.subcategory-link"
        )
        full_urls += [
            urljoin(BASE_URL, link.get("href")) for link in detail_page_urls
        ]

    return full_urls


def get_page_names_and_links(url: str) -> List[Tuple[str, str]]:
    pages = extract_all_urls(url)
    names = [
        page.split("/")[-1]
        if page.split("/")[-1] != "more" else "home" for page in pages
    ]
    names_and_links = list(zip(names, pages))

    return names_and_links


def parse_products_on_page(url: str, driver: webdriver) -> List[Product]:
    driver.get(url)

    cookies_accept_button = driver.find_elements(
        By.CLASS_NAME, "acceptCookies"
    )
    if cookies_accept_button:
        cookies_accept_button[0].click()

    scroll_button = driver.find_elements(
        By.CLASS_NAME,
        "ecomerce-items-scroll-more"
    )
    if scroll_button:
        while scroll_button[0].is_displayed():
            scroll_button[0].click()
            time.sleep(4)

    products = driver.find_elements(By.CLASS_NAME, "card-body")
    result = [parse_product_data(product) for product in products]

    return result


def write_to_csv_file(file_name: str, products: List[Product]) -> None:
    with open(file_name, "w", encoding="utf-8", newline="") as file:
        data = csv.writer(file)
        data.writerow([field.name for field in fields(Product)])
        data.writerows([astuple(product) for product in products])


def get_all_products() -> None:
    chrome_options = Options()
    chrome_options.add_argument("headless")
    with webdriver.Chrome(options=chrome_options) as g:
        pages = get_page_names_and_links(HOME_URL)
        for i, kiu in pages:
            all_products = parse_products_on_page(kiu, g)
            write_to_csv_file(i + ".csv", all_products)


if __name__ == "__main__":
    get_all_products()
