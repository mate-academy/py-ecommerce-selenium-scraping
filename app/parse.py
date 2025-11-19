import csv
from dataclasses import dataclass, fields, astuple
from urllib.parse import urljoin
from selenium import webdriver
from selenium.common import (
    NoSuchElementException,
    TimeoutException,
    ElementClickInterceptedException,
    ElementNotInteractableException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as ex_con
from selenium.webdriver.support.wait import WebDriverWait

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")
PAGES_TO_PARSE = {
    "home": "",
    "computers": "computers/",
    "laptops": "computers/laptops",
    "tablets": "computers/tablets",
    "phones": "phones/",
    "touch": "phones/touch",
}


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


PRODUCTS_FIELDS = [field.name for field in fields(Product)]


def get_single_product(product: WebElement) -> Product:
    return Product(
        title=product.find_element(
            By.CLASS_NAME,
            "title"
        ).get_attribute("title"),
        description=product.find_element(
            By.CLASS_NAME,
            "description"
        ).text,
        price=float(product.find_element(
            By.CLASS_NAME,
            "price"
        ).text.lstrip("$")),
        rating=len(product.find_elements(
            By.CLASS_NAME,
            "ws-icon-star"
        )),
        num_of_reviews=int(
            product.find_element(
                By.CSS_SELECTOR,
                '[itemprop="reviewCount"]'
            ).text
        ),
    )


def accept_cookies(driver: WebDriver) -> None:
    try:
        button = WebDriverWait(driver, 5).until(
            ex_con.element_to_be_clickable((By.CSS_SELECTOR, ".acceptCookies"))
        )
        try:
            button.click()
        except (
                ElementNotInteractableException,
                ElementClickInterceptedException
        ):
            driver.execute_script("arguments[0].click();", button)
    except (TimeoutException, NoSuchElementException):
        pass


def load_all_products(driver: WebDriver) -> None:
    while True:
        products_before = driver.find_elements(
            By.CSS_SELECTOR,
            ".product-wrapper"
        )
        try:
            button = WebDriverWait(driver, 2).until(
                ex_con.element_to_be_clickable(
                    (By.CSS_SELECTOR, ".ecomerce-items-scroll-more")
                )
            )
            driver.execute_script("arguments[0].scrollIntoView(true);", button)
            try:
                button.click()
            except (
                    ElementClickInterceptedException,
                    ElementNotInteractableException
            ):
                driver.execute_script("arguments[0].click();", button)

            WebDriverWait(driver, 3).until(
                lambda d: len(
                    d.find_elements(By.CSS_SELECTOR, ".product-wrapper")
                ) > len(products_before)
            )

        except (TimeoutException, NoSuchElementException):
            break


def get_page_products(driver: WebDriver, page_url: str) -> list[Product]:
    driver.get(page_url)
    accept_cookies(driver)
    load_all_products(driver)

    products = driver.find_elements(By.CSS_SELECTOR, ".product-wrapper")
    return [get_single_product(p) for p in products]


def write_products_to_csv(products: list[Product], file_name: str) -> None:
    with open(f"{file_name}.csv", "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(PRODUCTS_FIELDS)
        writer.writerows([astuple(p) for p in products])


def get_all_products() -> None:
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")

    with webdriver.Chrome(options=options) as driver:
        for category, path in PAGES_TO_PARSE.items():
            print(f"Scraping {category} page...")
            url = urljoin(HOME_URL, path)
            products = get_page_products(driver, url)
            write_products_to_csv(products, category)


if __name__ == "__main__":
    get_all_products()
