import csv
import logging
import sys
import time
from dataclasses import dataclass, fields, astuple
from typing import List, Optional
from urllib.parse import urljoin

from selenium import webdriver
from selenium.common import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement


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

_driver: WebDriver | None = None


def get_driver() -> WebDriver:
    return _driver


def set_driver(new_driver: WebDriver) -> None:
    global _driver
    _driver = new_driver


logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)8s]:  %(message)s",
    handlers=[
        logging.FileHandler("parser.log"),
        logging.StreamHandler(sys.stdout),
    ],
)


def parse_single_product(product_element: WebElement) -> Product:
    return Product(
        title=product_element.find_element(
            By.CSS_SELECTOR, ".title"
        ).get_attribute("title"),
        description=product_element.find_element(
            By.CSS_SELECTOR, ".description"
        ).text,
        price=float(product_element.find_element(
            By.CSS_SELECTOR, ".price"
        ).text.replace("$", "")),
        rating=len(product_element.find_elements(
            By.CSS_SELECTOR, ".ratings .ws-icon-star"
        )),
        num_of_reviews=int(product_element.find_element(
            By.CSS_SELECTOR, ".ratings > p.float-end"
        ).text.split()[0])
    )


def get_single_page_products(driver: WebDriver) -> list[Product]:
    product_elements = driver.find_elements(
        By.CSS_SELECTOR, ".thumbnail"
    )
    return [
        parse_single_product(product)
        for product in product_elements
    ]


def write_products_to_csv(products: [Product], filename: str) -> None:
    with open(filename, "w") as file:
        writer = csv.writer(file)
        writer.writerow(PRODUCT_FIELDS)
        writer.writerows([astuple(product) for product in products])


def scrape_products(
    driver: WebDriver,
    category_selector: str,
    filename: str,
    pagination_selector: Optional[str] = None
) -> List[Product]:
    logging.info(
        f"Start parsing {filename.replace(".csv", "")} products"
    )
    category_link = driver.find_element(By.CSS_SELECTOR, category_selector)
    driver.execute_script("arguments[0].click();", category_link)

    if pagination_selector:
        while True:
            try:
                more_button = driver.find_element(
                    By.CSS_SELECTOR, pagination_selector
                )
                if more_button.value_of_css_property("display") == "none":
                    raise NoSuchElementException(
                        "'More' button is no longer visible."
                    )

                logging.info("More button found, attempting to click.")
                driver.execute_script(
                    "arguments[0].click();", more_button
                )
            except NoSuchElementException:
                logging.info(
                    "Reached the last page of products "
                    "or 'More' button not found."
                )
                break

    products = get_single_page_products(driver)
    write_products_to_csv(products, filename)
    return products


def accept_cookies(driver: WebDriver) -> None:
    try:
        cookie_button = driver.find_element(
            By.CSS_SELECTOR,
            "#cookieBanner > div.acceptContainer > button"
        )
        cookie_button.click()
        logging.info("Cookie was successfully accepted")
    except NoSuchElementException:
        logging.info("Cookie accept button not found.")


def get_all_products() -> None:
    with webdriver.Chrome() as new_driver:
        set_driver(new_driver)
        driver = get_driver()
        driver.get(HOME_URL)

        # Accept cookies
        accept_cookies(driver)

        # Parse products for each category
        scrape_products(
            driver,
            "#side-menu a",
            "home.csv"
        )
        scrape_products(
            driver,
            "#side-menu li:nth-of-type(2) a",
            "computers.csv"
        )
        scrape_products(
            driver,
            "#side-menu li:nth-of-type(2) ul a",
            "laptops.csv",
            pagination_selector=".col-lg-9 > a"
        )
        scrape_products(
            driver,
            "#side-menu .nav-second-level li:nth-child(2) a",
            "tablets.csv",
            pagination_selector=".col-lg-9 > a"
        )
        scrape_products(
            driver,
            "#side-menu li:nth-of-type(3) a",
            "phones.csv"
        )
        scrape_products(
            driver,
            "#side-menu li:nth-of-type(3) ul a",
            "touch.csv",
            pagination_selector=".col-lg-9 > a"
        )


if __name__ == "__main__":
    start_time = time.time()
    get_all_products()
    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"Total time taken: {elapsed_time: .2f} seconds")
