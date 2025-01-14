import csv
import logging
import sys


from urllib.parse import urljoin
from dataclasses import dataclass, fields, astuple
from time import sleep

from selenium import webdriver
from selenium.common import (
    NoSuchElementException,
    ElementNotInteractableException,
    ElementClickInterceptedException
)
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.webdriver import WebDriver


BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")
COMPUTERS_URL = urljoin(HOME_URL, "computers")
PHONES_URL = urljoin(HOME_URL, "phones")
LAPTOPS_URL = urljoin(HOME_URL, "computers/laptops")
TABLETS_URL = urljoin(HOME_URL, "computers/tablets")
TOUCH_PHONES_URL = urljoin(HOME_URL, "phones/touch")

pages_to_parse = [
    HOME_URL, COMPUTERS_URL, PHONES_URL,
    LAPTOPS_URL, TABLETS_URL, TOUCH_PHONES_URL
]
file_names = ["home", "computers", "phones", "laptops", "tablets", "touch"]

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
    additional_info: dict | None = None


def parse_hdd_block_price(info: WebDriver) -> dict[str, float]:
    product_page = info.find_element(
        By.CSS_SELECTOR, "a"
    ).get_attribute("href")
    page_url = urljoin(BASE_URL, product_page)
    with webdriver.Chrome() as driver:
        driver.get(page_url)

        try:
            swatches = driver.find_element(By.CLASS_NAME, "swatches")
            if swatches:
                buttons = swatches.find_elements(By.TAG_NAME, "button")
                prices = {}
                for button in buttons:
                    if not button.get_property("disabled"):
                        button.click()
                        prices[button.get_property("value")] = float(
                            driver.find_element(
                                By.CLASS_NAME, "price"
                            ).text.replace("$", "")
                        )

                return prices

        except NoSuchElementException:
            pass
        except ElementClickInterceptedException:
            pass


logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)8s]:  %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("parser.log"),
    ],
)


def parse_single_product_info(product_info: WebDriver) -> Product | None:
    return Product(
        title=product_info.find_element(By.CLASS_NAME, "title").text,
        description=product_info.find_element(
            By.CLASS_NAME, "description"
        ).text,
        price=float(
            product_info.find_element(
                By.CLASS_NAME, "price"
            ).text.replace("$", "")
        ),
        num_of_reviews=int(
            product_info.find_element(
                By.CLASS_NAME, "review-count"
            ).text.split(" ")[0]
        ),
        rating=len(product_info.find_elements(
            By.CSS_SELECTOR, "span.ws-icon-star")
        ),
        additional_info={"hdd_prices": parse_hdd_block_price(product_info)},
    )


PRODUCT_FIELDS = [field.name for field in fields(Product)]


def get_single_page_product_info(page_driver: WebDriver) -> list[Product]:
    sleep(1)
    product_list = page_driver.find_elements(By.CLASS_NAME, "card-body")
    page_products = []
    for product_info in product_list:
        page_products.append(parse_single_product_info(product_info))
    return page_products


def get_all_products(url: str) -> list[Product]:
    driver = webdriver.Chrome()
    driver.get(url)
    sleep(3)
    cookies_button = driver.find_element(By.CLASS_NAME, "acceptCookies")
    if cookies_button:
        cookies_button.click()

    try:
        button = driver.find_element(
            By.CLASS_NAME,
            "ecomerce-items-scroll-more"
        )

        while button.is_displayed():
            button.click()
            sleep(0.1)

    except ElementNotInteractableException:
        pass

    except NoSuchElementException:
        pass

    except ElementClickInterceptedException:
        pass

    products = get_single_page_product_info(driver)
    driver.close()
    return products


def write_products_to_csv(output_csv_path: str, products: [Product]) -> None:
    with open(output_csv_path, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(PRODUCT_FIELDS)
        writer.writerows([astuple(product) for product in products])


def main() -> None:
    for i in range(len(pages_to_parse)):
        with webdriver.Chrome() as driver:
            set_driver(driver)
            logging.info(f"Start parsing {pages_to_parse[i]}")
            all_products_ = get_all_products(pages_to_parse[i])
            logging.info(f"End parsing {pages_to_parse[i]}")
            write_products_to_csv(f"{file_names[i]}.csv", all_products_)


if __name__ == "__main__":
    main()
