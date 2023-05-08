import csv
import time

from bs4 import BeautifulSoup
from dataclasses import dataclass, astuple, fields
from urllib.parse import urljoin
from selenium import webdriver
from selenium.common import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver


BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")
COMPUTERS_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/computers")
TABLETS_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/computers/tablets")
LAPTOPS_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/computers/laptops")
PHONES_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/phones")
TOUCH_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/phones/touch")

HOME_OUTPUT_CSV_PATH = "home.csv"
COMPUTERS_OUTPUT_CSV_PATH = "computers.csv"
TABLETS_OUTPUT_CSV_PATH = "tablets.csv"
LAPTOPS_OUTPUT_CSV_PATH = "laptops.csv"
PHONES_OUTPUT_CSV_PATH = "phones.csv"
TOUCH_OUTPUT_CSV_PATH = "touch.csv"

URLS = [
    (HOME_URL, HOME_OUTPUT_CSV_PATH),
    (COMPUTERS_URL, COMPUTERS_OUTPUT_CSV_PATH),
    (TABLETS_URL, TABLETS_OUTPUT_CSV_PATH),
    (LAPTOPS_URL, LAPTOPS_OUTPUT_CSV_PATH),
    (PHONES_URL, PHONES_OUTPUT_CSV_PATH),
    (TOUCH_URL, TOUCH_OUTPUT_CSV_PATH),
]


_driver: WebDriver | None = None


def get_driver() -> WebDriver:
    return _driver


def set_driver(driver: WebDriver) -> None:
    global _driver
    _driver = driver


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int
    additional_info: dict = None


PRODUCT_FIELDS = [field.name for field in fields(Product)]


def parse_hdd_block_prices(product: BeautifulSoup) -> dict:
    detail_url = urljoin(BASE_URL, product.select_one(".title")["href"])
    driver = get_driver()
    driver.get(detail_url)
    swatches = driver.find_element(By.CLASS_NAME, "swatches")
    buttons = swatches.find_elements(By.TAG_NAME, "button")

    prices = {}

    for button in buttons:
        if not button.get_property("disabled"):
            button.click()
            prices[button.get_property("value")] = float(
                driver.find_element(By.CLASS_NAME, "price").
                text.replace("$", "")
            )

    return prices


def parse_single_product(product: BeautifulSoup) -> Product:
    rating_element = product.select_one("p[data-rating]")
    rating = (
        int(rating_element["data-rating"])
        if rating_element is not None else len(
            product.select(".ratings > p > span"))
    )
    new_product = Product(
        title=product.select_one(".title")["title"],
        description=product.select_one(".description").text,
        price=float(product.select_one(".price").text.replace("$", "")),
        rating=rating,
        num_of_reviews=int(
            product.select_one("div.ratings > p.pull-right").text.split()[0]
        ),
    )
    try:
        hdd_priced = parse_hdd_block_prices(product)
    except NoSuchElementException:
        print(f"No hdd block in {new_product.title}")
        new_product.additional_info = new_product.price
    else:
        new_product.additional_info = hdd_priced
    return new_product


def accept_cookies(driver: webdriver) -> None:
    try:
        driver.find_element(By.CLASS_NAME, "acceptCookies").click()
    except NoSuchElementException:
        pass


def click_more(driver: webdriver) -> None:
    while True:
        try:
            time.sleep(0.1)
            driver.find_element(By.LINK_TEXT, "More").click()
        except NoSuchElementException:
            break


def get_all_products() -> None:
    driver = get_driver()
    for url, output_path in URLS:
        driver.get(url)
        accept_cookies(driver)
        click_more(driver)
        page = driver.page_source
        soup = BeautifulSoup(page, "html.parser")
        products = soup.select(".thumbnail")
        products_list = [parse_single_product(product) for product in products]
        write_products_to_csv(products_list, output_path)


def write_products_to_csv(products: [Product], output_path: str) -> None:
    with open(output_path, "w") as file:
        writer = csv.writer(file)
        writer.writerow(PRODUCT_FIELDS)
        writer.writerows([astuple(product) for product in products])


def main() -> None:
    with webdriver.Chrome() as driver:
        set_driver(driver)
        get_all_products()


if __name__ == "__main__":
    main()
