import csv
from dataclasses import dataclass, fields, astuple
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver


BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")

PRODUCT_PAGES = {
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

_driver: WebDriver | None = None


def get_driver() -> WebDriver:
    return _driver


def set_driver(new_driver: WebDriver) -> None:
    global _driver
    _driver = new_driver


def parse_single_product(product_soup: BeautifulSoup) -> Product:
    return Product(
        title=product_soup.select_one(".title")["title"],
        description=product_soup.select_one("p[class*=description]").text,
        price=float(product_soup.select_one("h4[class*=price]").text.replace("$", "")),
        rating=len(product_soup.select("span.ws-icon-star")),
        num_of_reviews=int(
            product_soup.select_one("p[class*=review-count]").text.split()[0]
        ),
    )


def accept_cookies(driver: WebDriver):
    try:
        accept_cookies_button = driver.find_element(By.CLASS_NAME, "acceptContainer")
        accept_cookies_button.click()
    except NoSuchElementException:
        pass


def get_products_from_page(url: str) -> list[Product]:
    driver = get_driver()
    driver.get(url)
    accept_cookies(driver)
    try:
        more_button = driver.find_element(By.CLASS_NAME, "btn-primary")
    except (NoSuchElementException, TimeoutException) as e:
        print(f"More button not found or timed out: {e}")
        more_button = None
    except Exception as e:
        print(f"Unexpected exception occurred: {e}")
        more_button = None

    if more_button:
        try:
            while more_button.is_displayed():
                driver.execute_script("arguments[0].click();", more_button)
        except Exception as e:
            print(f"Exception while clicking more button: {e}")

    soup = BeautifulSoup(driver.page_source, "html.parser")

    products = soup.select(".thumbnail")
    return [parse_single_product(product_soup) for product_soup in products]


def write_products_to_csv(products: [Product], csv_patch: str) -> None:
    with open(csv_patch, "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(PRODUCT_FIELDS)
        writer.writerows([astuple(product) for product in products])


def get_all_products() -> None:
    with webdriver.Chrome() as new_driver:
        set_driver(new_driver)
        for page_name, page_url in PRODUCT_PAGES.items():
            products = get_products_from_page(page_url)
            write_products_to_csv(products, f"{page_name}.csv")


if __name__ == "__main__":
    get_all_products()
