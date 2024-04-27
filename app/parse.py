import csv
import dataclasses
import time
from dataclasses import dataclass
from typing import List
from urllib.parse import urljoin

from selenium.common import NoSuchElementException
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver import Chrome, ChromeOptions
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec

BASE_URL = "https://webscraper.io/"

ENDPOINTS_URL = {
    "home": urljoin(BASE_URL, "test-sites/e-commerce/more/"),
    "computers": urljoin(BASE_URL, "/test-sites/e-commerce/more/computers/"),
    "laptops": urljoin(
        BASE_URL,
        "/test-sites/e-commerce/more/computers/laptops"
    ),
    "tablets": urljoin(
        BASE_URL,
        "/test-sites/e-commerce/more/computers/tablets"
    ),
    "phones": urljoin(BASE_URL, "/test-sites/e-commerce/more/phones"),
    "touch": urljoin(BASE_URL, "/test-sites/e-commerce/more/phones/touch")


}


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


PRODUCT_FIELDS = [filed.name for filed in dataclasses.fields(Product)]


def parse_single_product(product: WebElement) -> Product:

    return Product(
        title=product.find_element(
            By.CLASS_NAME, "title"
        ).text,
        description=product.find_element(
            By.CLASS_NAME, "description"
        ).text,
        price=float(product.find_element(
            By.CLASS_NAME, "price"
        ).text.replace("$", "")),
        rating=len(
            product.find_elements(
                By.CSS_SELECTOR,
                ".ratings > p:nth-of-type(2) > span"
            )
        ),
        num_of_reviews=int(
            product.find_element(
                By.CLASS_NAME, "review-count"
            ).text.split()[0]
        )
    )


def get_driver() -> WebDriver:
    web_options = ChromeOptions()
    web_options.add_argument("--headless")
    driver = Chrome(options=web_options)
    return driver


def accept_cookies(driver: WebDriver) -> None:
    cookies = driver.find_elements(By.CLASS_NAME, "acceptCookies")
    if cookies:
        WebDriverWait(driver, 10).until(
            ec.element_to_be_clickable((By.CLASS_NAME, "acceptCookies"))
        ).click()


def get_page_all_products(url: str) -> List[Product]:

    with get_driver() as driver:
        driver.get(url)
        accept_cookies(driver)
        get_more_products(driver)
        products = driver.find_elements(By.CLASS_NAME, "thumbnail")

        return [parse_single_product(products) for products in products]


def get_more_products(driver: WebDriver) -> None:
    while True:
        try:
            scroller_button = driver.find_element(
                By.CSS_SELECTOR, ".ecomerce-items-scroll-more"
            )
            if scroller_button.is_displayed():
                scroller_button.click()
                time.sleep(1)
            else:
                break
        except NoSuchElementException:
            break


def write_products_to_csv(filename: str, products: [Product]) -> None:
    with open(f"{filename}.csv", "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(PRODUCT_FIELDS)
        writer.writerows(
            [
                dataclasses.astuple(product)
                for product
                in products
            ]
        )


def get_all_products() -> None:
    for name_page, url in ENDPOINTS_URL.items():
        products = get_page_all_products(url)
        write_products_to_csv(name_page, products)


if __name__ == "__main__":
    start = time.time()
    get_all_products()
    end = time.time()
    print(f"Elapsed time: {end - start}")
