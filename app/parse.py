import csv
import time
from dataclasses import dataclass, astuple
from urllib.parse import urljoin

from selenium import webdriver
from selenium.common import NoSuchElementException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from tqdm import tqdm

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")
COMPUTERS_URL = urljoin(HOME_URL, "computers/")
LAPTOPS_URL = urljoin(COMPUTERS_URL, "laptops")
TABLETS_URL = urljoin(COMPUTERS_URL, "tablets")
PHONES_URL = urljoin(HOME_URL, "phones/")
TOUCH_URL = urljoin(PHONES_URL, "touch")

urls = {
    HOME_URL: "home",
    COMPUTERS_URL: "computers",
    LAPTOPS_URL: "laptops",
    TABLETS_URL: "tablets",
    PHONES_URL: "phones",
    TOUCH_URL: "touch",
}

PRODUCT_FIELDS = ["title", "description", "price", "rating", "num_of_reviews"]


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


def parse_single_product(product: WebElement):
    return Product(
        title=product.find_element(By.CLASS_NAME, "title").text,
        description=product.find_element(By.CLASS_NAME, "description").text,
        price=float(product.find_element(By.CLASS_NAME, "price").text.replace("$", "")),
        rating=len(product.find_elements(By.CLASS_NAME, "ws-icon-star")),
        num_of_reviews=int(
            product.find_element(By.CLASS_NAME, "review-count").text.split()[0]
        ),
    )


def parse_page_for_products(page_name: str, url: str):
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    driver = webdriver.Chrome(options=chrome_options)
    driver.get(url)

    try:
        accept_cookies_btn = driver.find_element(By.CLASS_NAME, "acceptCookies")
    except NoSuchElementException:
        pass
    else:
        accept_cookies_btn.click()

    try:
        more_button = driver.find_element(By.CLASS_NAME, "ecomerce-items-scroll-more")
    except NoSuchElementException:
        pass
    else:
        while more_button and more_button.is_displayed():
            more_button.click()
            time.sleep(0.1)

    product_elements = driver.find_elements(By.CLASS_NAME, "product-wrapper")

    products = [parse_single_product(product) for product in product_elements]

    write_products_to_csv(page_name, products)


def get_all_products() -> None:
    for url, page_name in tqdm(urls.items()):
        parse_page_for_products(page_name, url)


def write_products_to_csv(page: str, products: [Product]) -> None:
    with open(f"{page}.csv", "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(PRODUCT_FIELDS)
        writer.writerows([astuple(product) for product in products])


if __name__ == "__main__":
    time_start = time.perf_counter()
    get_all_products()
    execution_time = time.perf_counter() - time_start
    print(f"Execution time: {execution_time}")
