import requests
import csv

from dataclasses import dataclass, astuple
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common import (
    NoSuchElementException,
    ElementNotInteractableException,
    ElementClickInterceptedException
)
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver


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


def parse_single_product(product_soup: BeautifulSoup) -> Product:
    ratings_div = product_soup.find("div", class_="ratings")
    star_icons = len(
        ratings_div.find_all(
            "span",
            class_="ws-icon ws-icon-star"
        )
    )

    return Product(
        title=product_soup.select_one(".title")["title"],
        description=(
            product_soup
            .select_one(".description")
            .text.replace("\xa0", " ")
        ),
        price=float(product_soup.select_one(".price").text.replace("$", "")),
        rating=star_icons,
        num_of_reviews=int(product_soup.select_one(".ratings").text.split()[0])
    )


def get_single_product_page(soup: BeautifulSoup) -> [Product]:
    products = soup.select(".thumbnail")
    return [parse_single_product(product_soup) for product_soup in products]


def save_to_csv(products: list[Product], filename: str) -> None:
    with open(filename, "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(
            ["title", "description", "price", "rating", "num_of_reviews"]
        )
        writer.writerows([astuple(product) for product in products])


def click_more_button(driver: WebDriver) -> None:
    try:
        cookie = driver.find_element(By.CLASS_NAME, "acceptContainer")
        cookie.click()
    except NoSuchElementException:
        pass


def scrape_product_page(url: str, pagination: bool) -> list[Product]:
    soup = None
    if not pagination:
        content = requests.get(url).content
        soup = BeautifulSoup(content, "html.parser")

    if pagination:
        driver = get_driver()
        driver.get(url)

        click_more_button(driver)

        while True:
            more_button = driver.find_element(
                By.CSS_SELECTOR,
                "a.ecomerce-items-scroll-more"
            )
            try:
                more_button.click()
            except (
                    NoSuchElementException,
                    ElementNotInteractableException,
                    ElementClickInterceptedException
            ):
                break

        content = driver.page_source
        soup = BeautifulSoup(content, "html.parser")

    products = get_single_product_page(soup)
    return products


def scrape_and_save_products(
        pages: list[dict],
        pagination: bool = False
) -> None:
    for page in pages:
        url = urljoin(HOME_URL, page["url"])
        products = scrape_product_page(url, pagination)
        save_to_csv(products, f'{page["name"]}.csv')


def get_all_products() -> None:
    random_pages = [
        {"name": "home", "url": ""},
        {"name": "computers", "url": "computers/"},
        {"name": "phones", "url": "phones/"},
    ]

    pages_with_pagination = [
        {"name": "laptops", "url": "computers/laptops"},
        {"name": "tablets", "url": "computers/tablets"},
        {"name": "touch", "url": "phones/touch"},
    ]

    scrape_and_save_products(random_pages)

    with webdriver.Chrome() as new_driver:
        set_driver(new_driver)
        scrape_and_save_products(pages_with_pagination, pagination=True)


if __name__ == "__main__":
    get_all_products()
