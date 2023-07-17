import csv
from dataclasses import dataclass, astuple, fields
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup, Tag
from selenium import webdriver
from selenium.common import (
    NoSuchElementException,
    ElementNotInteractableException,
    ElementClickInterceptedException,
)
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


PRODUCT_FIELD = [field.name for field in fields(Product)]


def create_product_object(product_soup: Tag) -> Product:
    return Product(
        title=product_soup.select_one(".title")["title"],
        description=product_soup.select_one(
            ".description"
        ).text.replace(" ", " "),
        price=float(product_soup.select_one(".price").text.replace("$", "")),
        rating=len(product_soup.select(".ratings span")),
        num_of_reviews=int(
            product_soup.select_one(".ratings > p.pull-right").text.split()[0]
        )
    )


def get_single_data(url: str) -> list[Product]:
    driver = webdriver.Chrome()
    driver.get(url)

    accept_cookies_button = driver.find_elements(
        By.CSS_SELECTOR, ".acceptCookies"
    )
    if accept_cookies_button:
        accept_cookies_button[0].click()

    products = []

    while True:
        try:
            btn = driver.find_element(
                By.CLASS_NAME, "ecomerce-items-scroll-more"
            )
            btn.click()

        except (
                ElementNotInteractableException,
                NoSuchElementException,
                ElementClickInterceptedException
        ):
            soup = BeautifulSoup(
                driver.page_source, "html.parser"
            ).select(".thumbnail")
            products.extend(create_product_object(product) for product in soup)
            break

    driver.close()
    return products


def get_all_products_link(url: str) -> list[str]:
    data = requests.get(url).content
    soup = BeautifulSoup(data, "html.parser")
    return [url["href"] for url in soup.select(".subcategory-link")]


def get_link() -> list[str]:
    data = requests.get(HOME_URL).content
    soup = BeautifulSoup(data, "html.parser")
    url_pages = [li.select_one("a")["href"]
                 for li in soup.select("[id=side-menu] li")]

    for url in url_pages[1:]:
        all_products_url = get_all_products_link(urljoin(BASE_URL, url))

        for product in all_products_url:
            url_pages.append(product)

    return url_pages


def write_products_to_csv(products: dict[str | list]) -> None:
    for key, value in products.items():

        with open(f"{key}.csv", "w") as file:
            writer = csv.writer(file)
            writer.writerow(PRODUCT_FIELD)
            writer.writerows([astuple(product) for product in value])


def get_all_products() -> None:
    data = {}
    for url in get_link():
        url_list = url.split("/")

        if len(url_list) == 4:
            data["home"] = get_single_data(urljoin(BASE_URL, url))
        elif len(url_list) == 5:
            data[url_list[4]] = get_single_data(urljoin(BASE_URL, url))
        else:
            data[url_list[5]] = get_single_data(urljoin(BASE_URL, url))

    write_products_to_csv(data)


if __name__ == "__main__":
    get_all_products()
