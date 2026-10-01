import csv
from dataclasses import dataclass, fields, astuple
from urllib.parse import urljoin

import json

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.webdriver import WebDriver

options = webdriver.ChromeOptions()
options.add_argument("--headless=new")
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

BASE_URL = "https://webscraper.io/"

HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")
COMPUTERS_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/computers")
PHONES_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/phones")

LAPTOPS_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/computers/laptops")
TABLETS_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/computers/tablets")
TOUCH_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/phones/touch")

SINGLE_PRODUCT_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/product/")


URLS = {
    "HOME_URL": urljoin(
        BASE_URL, "test-sites/e-commerce/more/"
    ),
    "COMPUTERS_URL": urljoin(
        BASE_URL, "test-sites/e-commerce/more/computers"
    ),
    "PHONES_URL": urljoin(
        BASE_URL, "test-sites/e-commerce/more/phones"
    ),
    "LAPTOPS_URL": urljoin(
        BASE_URL, "test-sites/e-commerce/more/computers/laptops"
    ),
    "TABLETS_URL": urljoin(
        BASE_URL, "test-sites/e-commerce/more/computers/tablets"
    ),
    "TOUCH_URL": urljoin(
        BASE_URL, "test-sites/e-commerce/more/phones/touch"
    ),
}

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


PRODUCTS_FIELDS = [field.name for field in fields(Product)]


def parse_single_product_page(product_url: str) -> Product:
    driver = get_driver()
    driver.get(product_url)

    buttons = driver.find_elements(
        By.CSS_SELECTOR,
        '[data-termly-part="banner-actions"] button'
    )

    for button in buttons:
        if "Accept" in button.text:
            button.click()
            break

    return Product(
        title=driver.find_element(By.CLASS_NAME, "title").text,
        description=driver.find_element(By.CLASS_NAME, "description").text,
        price=float(
            "".join(
                driver.find_element(
                    By.CLASS_NAME, "price"
                ).text.replace("$", "")
            )
        ),
        rating=len(
            driver.find_elements(
                By.CSS_SELECTOR, ".ws-icon.ws-icon-star"
            )
        ),
        num_of_reviews=int(
            driver.find_element(
                By.CLASS_NAME, "review-count"
            ).text.strip().split()[0]
        ),
    )


def write_products_to_csv(
        products_cache: dict,
        file_name: str,
) -> None:
    with open(file_name, "w") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(PRODUCTS_FIELDS)
        writer.writerows([astuple(quote) for quote in products_cache.values()])


def get_all_products() -> None:
    with webdriver.Chrome(options=options) as driver:
        set_driver(driver)

        for name, url in URLS.items():
            driver.get(url)

            file_name = name.split("_")[0].lower() + ".csv"
            products_cache = {}

            products = driver.find_elements(
                By.CSS_SELECTOR, ".row.ecomerce-items.ecomerce-items-more"
            )

            if products:
                products_items = json.loads(
                    products[0].get_attribute("data-items")
                )

                for product_item in products_items:
                    product_url = urljoin(
                        SINGLE_PRODUCT_URL, str(product_item["id"])
                    )

                    if product_url not in products_cache:
                        products_cache[
                            str(product_url)
                        ] = parse_single_product_page(product_url)
            else:
                products = driver.find_elements(By.CLASS_NAME, "title")

                if products:
                    products_urls = [
                        product.get_attribute("href") for product in products
                    ]

                    for product_url in products_urls:

                        if product_url not in products_cache:
                            products_cache[str(product_url)] = (
                                parse_single_product_page(product_url)
                            )
            write_products_to_csv(products_cache, file_name)


if __name__ == "__main__":
    get_all_products()
