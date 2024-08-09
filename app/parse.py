import csv
import logging
from dataclasses import dataclass, fields, astuple
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common import NoSuchElementException, ElementNotInteractableException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

BASE_URL = "https://webscraper.io/"


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


def product_hdd_block_prices(product_soup: BeautifulSoup) -> dict[str, float]:
    detail_url = urljoin(BASE_URL, product_soup.select_one(".title")["href"])
    driver = get_driver()
    driver.get(detail_url)

    prices = {}
    try:
        swatches = driver.find_element(By.CLASS_NAME, "swatches")
        if swatches:
            buttons = swatches.find_elements(By.TAG_NAME, "button")
            for button in buttons:
                if not button.get_property("disabled"):
                    button.click()
                    prices[button.get_property("value")] = float(
                        driver.find_element(
                            By.CLASS_NAME, "price"
                        ).text.replace("$", ""))
    except NoSuchElementException:
        return prices

    return prices


def parse_single_product(product_soup: BeautifulSoup) -> Product:
    hdd_prices = product_hdd_block_prices(product_soup)
    return Product(
        title=product_soup.select_one(".title")["title"],
        description=product_soup.select_one(".description").text,
        price=float(product_soup.select_one(".price").text.replace("$", "")),
        rating=len(product_soup.select(".ratings span.ws-icon.ws-icon-star")),
        num_of_reviews=int(
            product_soup.select_one(".review-count").text.split()[0]
        ),
        additional_info={"hdd_prices": hdd_prices}
    )


def get_page_products(url: str, paginate: bool = False) -> [Product]:
    logging.info(f"Start scraping products from {url}")
    driver = get_driver()
    driver.get(url)

    if paginate:
        try:
            cookies = driver.find_element(By.CLASS_NAME, "acceptCookies")
            cookies.click()
        except ElementNotInteractableException as e:
            print(e)
        while True:
            try:
                more_button = driver.find_element(
                    By.CLASS_NAME,
                    "ecomerce-items-scroll-more"
                )
                more_button.click()
            except Exception as e:
                print(e)
    page_soup = BeautifulSoup(driver.page_source, "html.parser")
    product_soups = page_soup.select(".thumbnail")
    return [parse_single_product(product_soup)
            for product_soup in product_soups]


def write_products_to_csv(products: [Product], filename: str) -> None:
    with open(
            filename,
            "w",
            newline="",
            encoding="utf-8"
    ) as file:
        writer = csv.writer(file)
        writer.writerow(PRODUCT_FIELDS)
        for product in products:
            writer.writerow(astuple(product))


def get_all_products() -> None:
    with webdriver.Chrome() as new_driver:
        set_driver(new_driver)
        pages_info = {
            "home":
                {"path": "test-sites/e-commerce/more/",
                 "paginate": False},
            "computers":
                {"path": "test-sites/e-commerce/more/computers",
                 "paginate": False},
            "laptops":
                {"path": "test-sites/e-commerce/more/computers/laptops",
                 "paginate": True},
            "tablets":
                {"path": "test-sites/e-commerce/more/computers/tablets",
                 "paginate": True},
            "phones":
                {"path": "test-sites/e-commerce/more/phones",
                 "paginate": False},
            "touch":
                {"path": "test-sites/e-commerce/more/phones/touch",
                 "paginate": True}
        }

        for name, info in pages_info.items():
            url = urljoin(BASE_URL, info["path"])
            products = get_page_products(url, paginate=info["paginate"])
            filename = f"{name}.csv"
            write_products_to_csv(products, filename)
        new_driver.quit()


if __name__ == "__main__":
    get_all_products()
