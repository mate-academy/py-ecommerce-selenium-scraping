import csv
import time
from dataclasses import dataclass
from urllib.parse import urljoin

from selenium import webdriver
from selenium.common import NoSuchElementException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")
COMPUTERS_URL = urljoin(HOME_URL, "computers/")
LAPTOPS_URL = urljoin(COMPUTERS_URL, "laptops")
TABLETS_URL = urljoin(COMPUTERS_URL, "tablets")
PHONES_URL = urljoin(HOME_URL, "phones/")
TOUCH_URL = urljoin(PHONES_URL, "touch")
URLS = {
    "home": HOME_URL,
    "computers": COMPUTERS_URL,
    "laptops": LAPTOPS_URL,
    "tablets": TABLETS_URL,
    "phones": PHONES_URL,
    "touch": TOUCH_URL,
}


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


def get_chrome_driver() -> webdriver.Chrome:
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    driver = webdriver.Chrome(
        options=chrome_options, executable_path="chromedriver.exe"
    )
    return driver


def get_products_from_page(products: webdriver.Chrome) -> list:
    list_of_products = products.find_elements(By.CLASS_NAME, "thumbnail")
    result_products = []

    for product in list_of_products:
        result_products.append(
            Product(
                title=product.find_element(By.CLASS_NAME, "title").text,
                description=product.find_element(By.CLASS_NAME, "description").text,
                price=float(
                    product.find_element(By.CLASS_NAME, "price").text.replace("$", "")
                ),
                rating=len(product.find_elements(By.CLASS_NAME, "glyphicon")),
                num_of_reviews=int(
                    product.find_element(By.CLASS_NAME, "ratings").text.split()[0]
                ),
            )
        )

    return result_products


def write_products_to_file(products: list[Product], filename: str) -> None:
    with open(f"{filename}.csv", "w") as file:
        csv_writer = csv.writer(file)
        csv_writer.writerow(["title", "description", "price", "rating", "num_of_reviews"])

        for product in products:
            csv_writer.writerow(tuple(product.__dict__.values()))


def get_all_products() -> None:
    for file_name, url in URLS.items():
        with get_chrome_driver() as driver:
            driver.get(url)
            print(f"Getting products from {url}")
            try:
                button = driver.find_element(By.CLASS_NAME, "ecomerce-items-scroll-more")
                try:
                    cookies = driver.find_element(By.CLASS_NAME, "acceptCookies")
                    cookies.click()
                except NoSuchElementException:
                    continue
                while button.is_displayed():
                    button.click()
                    button = driver.find_element(By.CLASS_NAME, "ecomerce-items-scroll-more")
                    time.sleep(0.2)
            except NoSuchElementException:
                continue
            finally:
                write_products_to_file(
                    get_products_from_page(driver), file_name
                )


if __name__ == "__main__":
    get_all_products()
