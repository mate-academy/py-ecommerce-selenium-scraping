import csv
import random
import logging
import sys
from dataclasses import (
    dataclass,
    fields,
    astuple,
)
from urllib.parse import urljoin
import requests
from bs4 import (
    BeautifulSoup,
    Tag,
)
from selenium import webdriver
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
)


BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")
LAPTOP_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/computers/laptops/")

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
    additional_info: dict


PRODUCT_FIELDS = [f.name for f in fields(Product)]


logging.basicConfig(
    level=logging.DEBUG,
    format="[%(levelname)8s]:  %(message)s",
    handlers=[
        logging.FileHandler("products.log"),
        logging.StreamHandler(sys.stdout)
    ]
)


def parse_hdd_block_prices(product_soup: Tag) -> dict[str, float]:
    absolute_url = urljoin(HOME_URL, product_soup.select_one(".title")["href"])
    driver = get_driver()

    if driver is None:
        raise RuntimeError("WebDriver is not initialized. Call set_driver() first.")

    driver.get(absolute_url)

    wait = WebDriverWait(driver, 10)

    try:
        swatches = wait.until(
            EC.presence_of_element_located((By.CLASS_NAME, "swatches"))
        )
    except TimeoutException:
        return {}

    buttons = swatches.find_elements(By.TAG_NAME, "button")
    prices = {}

    for button in buttons:
        if not button.get_property("disabled"):
            button_value = button.get_property("value")
            button.click()

            try:
                wait.until(
                    EC.text_to_be_present_in_element(
                        (By.CLASS_NAME, "price"),
                        "$"
                    )
                )
                price_el = driver.find_element(By.CLASS_NAME, "price")
                prices[button_value] = float(price_el.text.replace("$", ""))
            except TimeoutException:
                logging.warning(f"Timeout waiting for price update on {absolute_url}")
            except NoSuchElementException:
                logging.warning(f"Price element not found on {absolute_url}")

    return prices


def parse_single_page_product(product: Tag) -> Product:
    if product.select_one(".swatches"):
        hdd_prices = parse_hdd_block_prices(product)
    else:
        hdd_prices = {}

    return Product(
        title=product.select_one(".title")["title"],
        description=product.select_one(".description").text,
        price=float(product.select_one(".price").text.replace("$", "")),
        rating=int(product.select_one("p[data-rating]")["data-rating"]),
        num_of_reviews=int(product.select_one(".review-count").text.split()[0]),
        additional_info={"hdd_prices": hdd_prices},
    )


def get_home_products() -> list[Product]:
    driver = get_driver()
    if driver is None:
        raise RuntimeError("WebDriver is not initialized. Call set_driver() first.")

    driver.get(HOME_URL)

    try:
        accept_btn = driver.find_element(By.ID, "accept-cookies")  # або By.CLASS_NAME/By.XPATH, залежить від сайту
        accept_btn.click()
    except NoSuchElementException:
        pass

    soup = BeautifulSoup(driver.page_source, "html.parser")
    products_elements = soup.select(".card-body")
    selected_products = random.sample(products_elements, 3)

    return [parse_single_page_product(product) for product in selected_products]


def get_num_pages(page_soup: Tag) -> int:
    pagination = page_soup.select_one(".pagination")
    if pagination is None:
        return 1
    return int(pagination.select("li")[-2].text)


def get_laptop_products_from_page(page_soup: Tag) -> list[Product]:
    products = page_soup.select(".card-body")
    return [parse_single_page_product(product) for product in products]


def get_laptop_page_products() -> list[Product]:
    driver = get_driver()
    if driver is None:
        raise RuntimeError("WebDriver is not initialized. Call set_driver() first.")

    LAPTOP_MORE_URL = urljoin(HOME_URL, "computers/laptops")
    driver.get(LAPTOP_MORE_URL)

    try:
        accept_btn = driver.find_element(By.ID, "accept-cookies")
        accept_btn.click()
    except NoSuchElementException:
        pass

    while True:
        try:
            more_button = driver.find_element(By.CLASS_NAME, "btn-primary")
            more_button.click()
            WebDriverWait(driver, 5).until(EC.staleness_of(more_button))
        except NoSuchElementException:
            break

    soup = BeautifulSoup(driver.page_source, "html.parser")
    products_elements = soup.select(".card-body")

    return [parse_single_page_product(product) for product in products_elements]


def write_products_to_csv(products: list[Product], filename: str) -> None:
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(PRODUCT_FIELDS)
        writer.writerows([astuple(product) for product in products])


def get_all_products() -> None:
    """Main entrypoint: scrape all pages and write results to CSV."""
    pages = {
        "home": get_home_products,
        "computers": get_computers_products,
        "laptops": get_laptop_page_products,
        "tablets": get_tablets_products,
        "phones": get_phones_products,
        "touch": get_touch_products,
    }

    with webdriver.Chrome() as driver:
        set_driver(driver)

        for name, func in pages.items():
            logging.info(f"Parsing {name} page")
            products = func()
            write_products_to_csv(products, f"{name}.csv")
            logging.info(f"Saved {len(products)} products to {name}.csv")


def main() -> None:
    get_all_products()


if __name__ == "__main__":
    main()
