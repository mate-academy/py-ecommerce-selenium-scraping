import csv
from dataclasses import dataclass, fields, astuple
from urllib.parse import urljoin
from selenium import webdriver
from selenium.common import (
    ElementNotInteractableException,
    ElementClickInterceptedException,
    NoSuchElementException
)
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")
COMPUTERS_URL = urljoin(HOME_URL, "computers/")
LAPTOPS_URL = urljoin(COMPUTERS_URL, "laptops")
TABLETS_URL = urljoin(COMPUTERS_URL, "tablets")
PHONES_URL = urljoin(HOME_URL, "phones/")
TOUCH_URL = urljoin(PHONES_URL, "touch")


driver_options = Options()
driver_options.add_argument("--headless")
driver_options.add_argument("--disable-gpu")
driver_options.add_argument("--disable-dev-shm-usage")

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


PRODUCT_FIELDS = [field.name for field in fields(Product)]


def get_single_product_info(card_info: WebElement) -> dict:
    print("Start write info for product")
    product_info = {
        "title": card_info.find_element(
            By.CLASS_NAME, "title"
        ).get_attribute("title"),
        "description": card_info.find_element(
            By.CLASS_NAME, "description"
        ).text,
        "price": card_info.find_element(
            By.CLASS_NAME, "price"
        ).text.replace("$", ""),
        "rating": len(card_info.find_elements(
            By.CSS_SELECTOR, ".ratings p span.ws-icon-star")),
        "num_of_reviews": card_info.find_element(
            By.CLASS_NAME, "review-count"
        ).text.split()[0],
    }
    return product_info


def get_products(url_for_parse: str) -> [Product]:
    print(f"Start parse: {url_for_parse}")
    driver = get_driver()
    driver.get(url_for_parse)
    print("Check cookies button")
    try:
        accept_button = driver.find_element(By.CLASS_NAME, "acceptCookies")
        if accept_button:
            print("Click on cookies button")
            accept_button.click()
    except NoSuchElementException:
        print("Cookies accept button not found")

    try:
        print("Check More button")
        more_button = driver.find_element(
            By.CLASS_NAME,
            "ecomerce-items-scroll-more"
        )
        while True:
            if more_button.value_of_css_property("display") == "none":
                break
            more_button.click()
            print("Click on More button")
            more_button = driver.find_element(
                By.CLASS_NAME,
                "ecomerce-items-scroll-more"
            )
    except (ElementNotInteractableException,
            ElementClickInterceptedException,
            NoSuchElementException
            ):
        print("End of page")

    products_cards = driver.find_elements(By.CLASS_NAME, "thumbnail")
    products = []
    for card in products_cards:
        product = get_single_product_info(card)
        print("Create Product and add to all")
        products.append(Product(
            title=product["title"],
            description=product["description"],
            price=float(product["price"]),
            rating=int(product["rating"]),
            num_of_reviews=int(product["num_of_reviews"]),
        ))
    print("Return list of Products")
    return products


def write_products_to_csv(csv_name: str, products: [Product]) -> None:
    with open(csv_name, "w", newline="", encoding="utf-8") as f:
        print(f"Start write in {csv_name}")
        writer = csv.writer(f)
        writer.writerow(PRODUCT_FIELDS)
        writer.writerows([astuple(product) for product in products])
        print(f"End write in {csv_name}")


def get_all_products() -> None:
    with webdriver.Chrome(driver_options) as driver:
        set_driver(driver)
        write_products_to_csv("home.csv", get_products(HOME_URL))
        write_products_to_csv("computers.csv", get_products(COMPUTERS_URL))
        write_products_to_csv("laptops.csv", get_products(LAPTOPS_URL))
        write_products_to_csv("tablets.csv", get_products(TABLETS_URL))
        write_products_to_csv("phones.csv", get_products(PHONES_URL))
        write_products_to_csv("touch.csv", get_products(TOUCH_URL))


if __name__ == "__main__":
    get_all_products()
