import csv
import time

import requests
from dataclasses import dataclass, fields, astuple
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common import NoSuchElementException
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from tqdm import tqdm


BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int
    additional_info: dict


PRODUCT_FIELDS = [field.name for field in fields(Product)]

_driver: WebDriver | None = None


def get_driver() -> WebDriver:
    return _driver


def set_driver(new_driver: WebDriver) -> None:
    global _driver
    _driver = new_driver


def parse_hdd_block_prices(product_soup: BeautifulSoup) -> dict[str, float]:
    detailed_url = urljoin(BASE_URL, product_soup.select_one(".title")["href"])
    driver = get_driver()
    driver.get(detailed_url)
    try:
        swatches = driver.find_element(By.CLASS_NAME, "swatches")
        buttons = swatches.find_elements(By.TAG_NAME, "button")
        prices = {}
        for button in buttons:
            if not button.get_property("disabled"):
                button.click()
                prices[button.get_property("value")] = float(
                    driver.find_element(By.CLASS_NAME, "price").text.replace("$", ""))

        return prices
    except:
        pass


def parse_single_product(product_soup: BeautifulSoup) -> Product:
    hdd_prices = parse_hdd_block_prices(product_soup)
    return Product(
        title=product_soup.select_one(".title")["title"],
        description=product_soup.select_one(".description").text,
        price=float(product_soup.select_one(".price").text.replace("$", "")),
        rating=len(product_soup.select("div.ratings > p > span.ws-icon.ws-icon-star")),
        num_of_reviews=int(product_soup.select_one(
            ".ratings > p.pull-right"
        ).text.split()[0]),
        additional_info={"hdd_prices": hdd_prices},
    )


def accept_cookie(driver):
    try:
        cookie_button = driver.find_element(By.CLASS_NAME, "acceptCookies")
        cookie_button.click()
        time.sleep(0.5)
    except NoSuchElementException:
        pass


def more_button(url: str) -> BeautifulSoup:
    options = Options()
    options.add_argument("--headless")
    driver = webdriver.Edge(options=options)
    driver.get(url)

    try:
        more_but = driver.find_element(By.CLASS_NAME, "ecomerce-items-scroll-more")
    except NoSuchElementException:
        more_but = None

    while more_but:
        if more_but.is_displayed() is False:
            break
        driver.execute_script("arguments[0].click();", more_but)

    return BeautifulSoup(driver.page_source, "html.parser")


def get_single_page_products(url: str) -> [Product]:
    soup = more_button(url)
    products = soup.select(".thumbnail")

    products_list = []
    for product_soup in tqdm(products, desc=f"Scraping Products on {url}"):
        product = parse_single_product(product_soup)
        products_list.append(product)

    return products_list


def write_products_to_csv(csv_output_path: str, products: [Product]) -> None:
    with open(csv_output_path, "w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(PRODUCT_FIELDS)
        writer.writerows([astuple(product) for product in products])


def main(csv_output_path: str, url: str):
    with webdriver.Edge() as new_driver:
        set_driver(new_driver)
        products = get_single_page_products(url)
        write_products_to_csv(csv_output_path, products)


if __name__ == "__main__":
    main("home.csv", HOME_URL)
    main("random_computers.csv", urljoin(BASE_URL, "test-sites/e-commerce/more/computers"))
    main("laptops.csv", urljoin(BASE_URL, "test-sites/e-commerce/more/computers/laptops"))
    main("tablets.csv", urljoin(BASE_URL, "test-sites/e-commerce/more/computers/tablets"))
    main("random_phones.csv", urljoin(BASE_URL, "test-sites/e-commerce/more/phones"))
    main("phones_touch.csv", urljoin(BASE_URL, "test-sites/e-commerce/more/phones/touch"))
