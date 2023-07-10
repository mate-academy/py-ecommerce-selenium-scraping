import csv
from dataclasses import dataclass, astuple, fields
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.webdriver import WebDriver
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


def get_page_soup(link: str) -> BeautifulSoup:
    page = requests.get(link).content
    return BeautifulSoup(page, "html.parser")


def get_pages_for_parsing() -> dict[str, str]:
    page_soup = get_page_soup(HOME_URL)

    links = {}

    nav = page_soup.select_one(".sidebar")
    nav_links = nav.select("a")

    for link in nav_links:
        links[link.text.strip().lower()] = urljoin(BASE_URL, link["href"])
        soup = get_page_soup(urljoin(BASE_URL, link["href"]))

        second_level_link = soup.select_one(".nav-second-level")
        if second_level_link:
            a_dict = {
                a.text.strip().lower(): urljoin(BASE_URL, a["href"])
                for a in second_level_link.select("a")
            }
            links.update(a_dict)

    return links


def parse_single_product(product_soup: BeautifulSoup) -> Product:
    return Product(
        title=product_soup.select_one(".title")["title"],
        description=product_soup.select_one(".description").text,
        price=float(product_soup.select_one(".price").text.replace("$", "")),
        rating=int(len(product_soup.select(".glyphicon.glyphicon-star"))),
        num_of_reviews=int(product_soup.select_one(
            ".ratings > p.pull-right"
        ).text.split()[0]),
    )


def collect_one_page_products(url: str) -> list[Product]:
    products_soup = get_page_soup(url)
    products = products_soup.select(".thumbnail")

    return [parse_single_product(product_soup) for product_soup in products]


def click_more_btn(url: str, driver: WebDriver) -> WebDriver:
    driver.get(url)
    driver.maximize_window()

    try:
        accept_cookies_button = driver.find_element(
            By.CLASS_NAME, "acceptCookies"
        )
        if accept_cookies_button:
            accept_cookies_button.click()
    except Exception:
        pass

    more_button = driver.find_element(
        By.CLASS_NAME,
        "ecomerce-items-scroll-more"
    )

    try:
        while not more_button.value_of_css_property("display") == "none":
            more_button.click()
    except Exception:
        pass

    return driver


def collect_products(name: str, url: str, driver: WebDriver) -> list[Product]:
    if name in ("home", "computers", "phones"):
        return collect_one_page_products(url)

    driver = click_more_btn(url, driver)
    soup = BeautifulSoup(driver.page_source, "html.parser")
    products = soup.select(".thumbnail")
    return [parse_single_product(product_soup) for product_soup in products]


def write_products_to_csv(name: str, products: list[Product]) -> None:
    with open(f"{name}.csv", "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(PRODUCT_FIELDS)
        writer.writerows([astuple(product) for product in products])


def get_all_products() -> None:
    driver = webdriver.Chrome()
    pages = get_pages_for_parsing()
    for name, url in pages.items():
        products = collect_products(name, url, driver)
        write_products_to_csv(name, products)
    driver.close()


if __name__ == "__main__":
    get_all_products()
