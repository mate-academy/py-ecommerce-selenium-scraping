import csv
import time
from dataclasses import dataclass, fields, asdict
from urllib.parse import urljoin

from selenium import webdriver
from selenium.common import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")
COMPUTERS_URL = urljoin(HOME_URL, "computers/")
LAPTOPS_URL = urljoin(COMPUTERS_URL, "laptops")
TABLETS_URL = urljoin(COMPUTERS_URL, "tablets")
PHONES_URL = urljoin(HOME_URL, "phones/")
TOUCH_URL = urljoin(PHONES_URL, "touch")


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


PRODUCT_FIELDS = [field.name for field in fields(Product)]


def scrape_single_product(product_element: WebElement) -> Product:
    return Product(
        title=product_element.find_element(
            By.CLASS_NAME, "title"
        ).get_attribute("title"),
        description=product_element.find_element(
            By.CLASS_NAME, "description"
        ).text,
        price=float(
            product_element.find_element(
                By.CLASS_NAME, "price"
            ).text.replace("$", "")
        ),
        rating=len(
            product_element.find_elements(
                By.CSS_SELECTOR, ".ratings > p:nth-of-type(2) > span"
            )
        ),
        num_of_reviews=int(
            product_element.find_element(
                By.CLASS_NAME, "review-count"
            ).text.split(" ")[0]
        )
    )


def is_more_button_on_page(driver: webdriver) -> bool:
    try:
        more_button = driver.find_element(
            By.CLASS_NAME, "ecomerce-items-scroll-more"
        )
        return more_button.is_displayed()
    except NoSuchElementException:
        return False


def scroll_page(driver: webdriver) -> None:
    while is_more_button_on_page(driver):
        more_button = driver.find_element(
            By.CLASS_NAME, "ecomerce-items-scroll-more"
        )
        more_button.click()
        time.sleep(0.25)


def accept_cookies(driver: webdriver) -> None:
    try:
        accept_button = driver.find_element(By.CLASS_NAME, "acceptCookies")
        accept_button.click()
    except NoSuchElementException:
        return


def scrape_whole_page(driver: webdriver) -> list[Product]:
    accept_cookies(driver)
    scroll_page(driver)
    products = driver.find_elements(By.CLASS_NAME, "card-body")

    return [
        scrape_single_product(product)
        for product in products
    ]


def write_to_csv(filename: str, products: list[Product]) -> None:
    with open(filename, "w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(PRODUCT_FIELDS)
        writer.writerows([asdict(product).values() for product in products])


def get_all_products() -> None:
    driver = webdriver.Chrome()
    urls = {
        "home": HOME_URL,
        "computers": COMPUTERS_URL,
        "laptops": LAPTOPS_URL,
        "tablets": TABLETS_URL,
        "phones": PHONES_URL,
        "touch": TOUCH_URL
    }
    for filename, url in urls.items():
        driver.get(url)
        write_to_csv(f"{filename}.csv", scrape_whole_page(driver))


if __name__ == "__main__":
    get_all_products()
