import csv

from dataclasses import dataclass, fields, astuple
from urllib.parse import urljoin

from selenium import webdriver
from selenium.common import TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")

pages = {
    "home": HOME_URL,
    "computers": urljoin(HOME_URL, "computers/"),
    "laptops": urljoin(HOME_URL, "computers/laptops"),
    "tablets": urljoin(HOME_URL, "computers/tablets"),
    "phones": urljoin(HOME_URL, "phones/"),
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


def handle_cookies(driver: WebDriver) -> None:
    try:
        cookies_button = WebDriverWait(driver, 1).until(
            expected_conditions.element_to_be_clickable(
                (By.CLASS_NAME, "acceptCookies")
            )
        )
        cookies_button.click()
    except Exception:
        pass


def click_more_button(driver: WebDriver) -> None:
    try:
        more_button = WebDriverWait(driver, 1).until(
            expected_conditions.element_to_be_clickable(
                (By.CLASS_NAME, "ecomerce-items-scroll-more")
            )
        )
        more_button.click()
    except TimeoutException:
        pass


def handle_more_button(driver: WebDriver) -> None:
    previous_product_elements = len(
        driver.find_elements(By.CLASS_NAME, "thumbnail")
    )
    counter = 0

    while counter < 5:
        try:
            click_more_button(driver)
            current_product_elements = len(
                driver.find_elements(By.CLASS_NAME, "thumbnail")
            )

            if current_product_elements != previous_product_elements:
                counter = 0
                continue

            counter += 1
            previous_product_elements = current_product_elements
        except Exception:
            break


def parse_single_product(product_elements: [WebElement]) -> [Product]:
    products = []

    for product_element in product_elements:
        products.append(
            Product(
                title=product_element.find_element(
                    By.CLASS_NAME, "title"
                ).get_property("title"),
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
                        By.CLASS_NAME, "ws-icon-star"
                    )
                ),
                num_of_reviews=int(
                    product_element.find_element(
                        By.CLASS_NAME, "review-count"
                    ).text.split()[0]
                ),
            )
        )

    return products


def parse_page_products(url: str, driver: WebDriver) -> [Product]:
    driver.get(url)

    handle_cookies(driver)
    handle_more_button(driver)

    product_elements = driver.find_elements(By.CLASS_NAME, "thumbnail")
    products = parse_single_product(product_elements)

    return products


def write_products_to_csv(products: [Product], page: str) -> None:
    with open(f"{page}.csv", "w", newline="") as file:
        writer = csv.writer(file, lineterminator="\n")
        writer.writerow(PRODUCT_FIELDS)
        writer.writerows([astuple(product) for product in products])


def get_all_products() -> None:
    chrome_options = Options()
    chrome_options.add_argument("headless")
    driver = webdriver.Chrome(options=chrome_options)

    for page, url in pages.items():
        products = parse_page_products(url, driver)
        write_products_to_csv(products, page)


if __name__ == "__main__":
    get_all_products()
