import csv
import time
from dataclasses import dataclass, fields, astuple
from urllib.parse import urljoin

from selenium import webdriver
from selenium.common.exceptions import (
    NoSuchElementException,
    StaleElementReferenceException,
    TimeoutException,
)
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.wait import WebDriverWait
from tqdm import tqdm


BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")

COOKIES_ACCEPT_XPATH = (
    "//button[contains(., 'Accept')] | //a[contains(., 'Accept')]"
)

URLS = {
    "home": HOME_URL,
    "computers": urljoin(HOME_URL, "computers"),
    "laptops": urljoin(HOME_URL, "computers/laptops"),
    "tablets": urljoin(HOME_URL, "computers/tablets"),
    "phones": urljoin(HOME_URL, "phones"),
    "touch": urljoin(HOME_URL, "phones/touch"),
}


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


PRODUCT_FIELDS = [field.name for field in fields(Product)]


def parse_single_product(product_element: WebElement) -> Product:
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
            product_element.find_elements(By.CLASS_NAME, "ws-icon-star")
        ),
        num_of_reviews=int(
            product_element.find_element(
                By.CLASS_NAME, "review-count"
            ).text.split()[0]
        ),
    )


def js_click(driver: WebDriver, element: WebElement) -> None:
    driver.execute_script("arguments[0].click();", element)


def accept_cookies_if_needed(driver: WebDriver) -> None:
    try:
        accept_button = WebDriverWait(driver, 5).until(
            ec.element_to_be_clickable((By.XPATH, COOKIES_ACCEPT_XPATH))
        )
        js_click(driver, accept_button)
        WebDriverWait(driver, 5).until(
            ec.invisibility_of_element(accept_button)
        )
    except TimeoutException:
        pass


def click_show_more_if_present(driver: WebDriver) -> None:
    while True:
        try:
            more_button = driver.find_element(
                By.CLASS_NAME, "ecomerce-items-scroll-more"
            )

            if not more_button.is_displayed():
                return

            js_click(driver, more_button)
            time.sleep(0.5)
        except NoSuchElementException:
            return
        except StaleElementReferenceException:
            continue


def parse_single_page(driver: WebDriver, url: str) -> list[Product]:
    driver.get(url)
    accept_cookies_if_needed(driver)
    click_show_more_if_present(driver)

    product_elements = driver.find_elements(By.CLASS_NAME, "thumbnail")
    return [
        parse_single_product(product_element)
        for product_element in product_elements
    ]


def write_products_to_csv(products: list[Product], file_name: str) -> None:
    with open(file_name, "w", newline="") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(PRODUCT_FIELDS)
        writer.writerows([astuple(product) for product in products])


def get_all_products() -> None:
    options = Options()
    options.add_argument("--headless=new")

    with webdriver.Chrome(options=options) as driver:
        for page_name, page_url in tqdm(
            URLS.items(), desc="Scraping pages", unit="page"
        ):
            products = parse_single_page(driver, page_url)
            write_products_to_csv(products, f"{page_name}.csv")


if __name__ == "__main__":
    get_all_products()
