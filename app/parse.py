import csv
from dataclasses import dataclass, fields
from urllib.parse import urljoin

from selenium.common import NoSuchElementException, TimeoutException
from selenium.webdriver import Chrome

from bs4 import BeautifulSoup, Tag
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")
COMPUTERS_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/computers")
LAPTOPS_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/computers/laptops")
TABLETS_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/computers/tablets")
PHONES_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/phones")
TOUCH_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/phones/touch")

_driver: WebDriver | None = None


def get_driver() -> None:
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


PRODUCT_FIELDS = [field.name for field in fields(Product)]


def parse_single_product(product: Tag) -> Product:
    return Product(
        title=product.select_one(".title")["title"],
        description=(
            product.select_one(".description").get_text()
            .replace("B\xa0", " ")
            .replace("\xa0", " ")
            .strip()
        ),
        price=float(product.select_one(".price").text.replace("$", "")),
        rating=len(product.select(
            ".ws-icon-star"
        )),
        num_of_reviews=int(product.select_one(".review-count")
                           .text.split()[0]),
    )


def accept_cookies(driver: WebDriver) -> None:
    try:
        WebDriverWait(driver, 2).until(
            ec.element_to_be_clickable((By.CLASS_NAME, "acceptCookies"))
        ).click()
    except Exception:
        pass


def parse_products_from_page(driver: WebDriver) -> list[Product]:
    product_selector = ".product-wrapper.card-body"

    WebDriverWait(driver, 10).until(
        lambda d: len(d.find_elements(By.CSS_SELECTOR, product_selector)) > 0
    )

    while True:
        current_count = len(
            driver.find_elements(By.CSS_SELECTOR, product_selector)
        )

        try:
            button = driver.find_element(
                By.CSS_SELECTOR, ".ecomerce-items-scroll-more"
            )
        except NoSuchElementException:
            break

        driver.execute_script("arguments[0].click();", button)

        try:
            WebDriverWait(driver, 5).until(
                lambda d: len(
                    d.find_elements(By.CSS_SELECTOR, product_selector)
                ) > current_count
            )
        except TimeoutException:
            break

    elements = driver.find_elements(By.CSS_SELECTOR, product_selector)

    products = []

    for element in elements:
        soup = BeautifulSoup(element.get_attribute("outerHTML"), "html.parser")
        products.append(parse_single_product(soup))

    return products


def write_to_csv(products: list[Product], page_name: str) -> None:
    with open(page_name, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(PRODUCT_FIELDS)

        for product in products:
            row = [
                getattr(product, field_name)
                for field_name in PRODUCT_FIELDS
            ]

            writer.writerow(row)


def get_all_products() -> None:
    driver = Chrome()
    set_driver(driver)

    pages = {
        "home": HOME_URL,
        "computers": COMPUTERS_URL,
        "laptops": LAPTOPS_URL,
        "tablets": TABLETS_URL,
        "phones": PHONES_URL,
        "touch": TOUCH_URL,
    }

    try:
        for page_name, url in pages.items():
            driver.get(url)
            accept_cookies(driver)
            products = parse_products_from_page(driver)

            write_to_csv(products, f"{page_name}.csv")
    finally:
        driver.quit()


if __name__ == "__main__":
    get_all_products()
