import time
from dataclasses import dataclass
from urllib.parse import urljoin
import csv
from selenium.webdriver.support import expected_conditions as ec
from dataclasses import astuple
from dataclasses import fields
from selenium import webdriver
from selenium.common import NoSuchElementException, TimeoutException
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.wait import WebDriverWait

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")
PAGES = {
    "home": HOME_URL,
    "computers": urljoin(HOME_URL, "computers"),
    "laptops": urljoin(HOME_URL, "computers/laptops"),
    "tablets": urljoin(HOME_URL, "computers/tablets"),
    "phones": urljoin(HOME_URL, "phones"),
    "touch": urljoin(HOME_URL, "phones/touch"),
}

ACCEPT_COOKIES = ""


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


PRODUCT_FIELDS = [field.name for field in fields(Product)]


def click_accept_cookie(driver: WebDriver) -> None:
    driver.get(HOME_URL)
    try:
        button = driver.find_element(By.CLASS_NAME, "t-acceptAllButton")
        button.click()
        time.sleep(1)
    except NoSuchElementException:
        pass


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
            product_element.find_elements(
                By.CSS_SELECTOR, ".ratings .ws-icon-star"
            )
        ),
        num_of_reviews=int(
            product_element.find_element(
                By.CSS_SELECTOR, ".ratings span[itemprop]"
            ).text
        ),
    )


def parse_page(driver: WebDriver, url: str) -> list[Product]:
    driver.get(url)

    while True:
        try:
            more = WebDriverWait(driver, 5).until(
                ec.element_to_be_clickable(
                    (By.CLASS_NAME, "ecomerce-items-scroll-more")
                )
            )
        except TimeoutException:
            break

        products = driver.find_elements(By.CLASS_NAME, "card-body")
        old_count = len(products)

        driver.execute_script(
            "arguments[0].scrollIntoView({block: 'center'});",
            more
        )

        more.click()

        WebDriverWait(driver, 10).until(
            lambda d: len(
                d.find_elements(By.CLASS_NAME, "card-body")
            ) > old_count
        )

    product_elements = driver.find_elements(
        By.CLASS_NAME, "card-body"
    )
    result = []

    for product_element in product_elements:
        product = parse_single_product(product_element)
        result.append(product)
    return result


def write_to_csvfile(products: list[Product], output_csv_path: str) -> None:
    with open(output_csv_path, "w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(PRODUCT_FIELDS)
        writer.writerows(astuple(product) for product in products)


def get_all_products() -> None:
    with webdriver.Chrome() as driver:
        click_accept_cookie(driver)
        for name, url in PAGES.items():
            products = parse_page(driver, url)
            write_to_csvfile(products, f"{name}.csv")


if __name__ == "__main__":
    get_all_products()
