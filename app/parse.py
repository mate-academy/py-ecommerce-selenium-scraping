import time
from dataclasses import dataclass
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common import (
    NoSuchElementException,
    TimeoutException,
    ElementNotInteractableException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as exc
from selenium.webdriver.support.wait import WebDriverWait

from app import writer
from app.generator import CSVGenerator

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")
COMPUTERS_URL = urljoin(HOME_URL, "computers")
LAPTOPS_URL = COMPUTERS_URL + "/laptops"
TABLETS_URL = COMPUTERS_URL + "/tablets"
PHONES_URL = urljoin(HOME_URL, "phones")
TOUCH_URL = PHONES_URL + "/touch"

URLS = [
    HOME_URL,
    COMPUTERS_URL,
    LAPTOPS_URL,
    TABLETS_URL,
    PHONES_URL,
    TOUCH_URL,
]


def init_driver() -> webdriver.Chrome:
    driver = webdriver.Chrome()
    return driver


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


def product_parse(
        driver: webdriver.Chrome,
        product_soup: BeautifulSoup
) -> Product:
    detailed_url = urljoin(
        BASE_URL,
        product_soup.select_one(".title")["href"]
    )
    driver.get(detailed_url)
    title = (
        driver.find_element(By.CLASS_NAME, "title")
        .text.strip()
    )
    return Product(
        title=title,
        description=product_soup.find(
            "p", {"class": "description"}
        )
        .text.strip()
        .replace("\xa0", " ")
        .strip(),
        price=float(
            product_soup.find("h4", {"class": "price"})
            .text.strip()
            .replace("$", "")
        ),
        rating=int(len(product_soup.find_all(
            "span", class_="ws-icon-star"))
        ),
        num_of_reviews=int(
            product_soup.find("p", {"class": "review-count"})
            .text.strip()
            .split()[0]
        ),
    )


def load_full_page(
        driver: webdriver.Chrome,
        url: str
) -> BeautifulSoup:
    driver.get(url)

    try:
        accept_button = WebDriverWait(driver, 2).until(
            exc.element_to_be_clickable((By.CLASS_NAME, "acceptCookies"))
        )
        accept_button.click()
        print("Cookies accepted")
    except (TimeoutException, NoSuchElementException):
        print("Cookies not found")

    while True:
        try:
            more_button = WebDriverWait(driver, 2).until(
                exc.presence_of_element_located(
                    (By.CLASS_NAME, "ecomerce-items-scroll-more")
                )
            )
            if (
                    "disabled" not in more_button.get_attribute("class")
                    and more_button.is_displayed()
            ):
                more_button.click()
                time.sleep(2)
            else:
                break
        except (
                NoSuchElementException,
                ElementNotInteractableException,
                TimeoutException,
        ):
            break

    return BeautifulSoup(driver.page_source, "html.parser")


def get_products(
        driver: webdriver.Chrome,
        url: str
) -> list[Product]:
    all_products = []
    soup = load_full_page(driver, url)
    products = soup.find_all(
        "div", {"class": "col-md-4 col-xl-4 col-lg-4"}
    )
    for product in products:
        all_products.append(product_parse(driver, product))
    return all_products


def write_to_csv(path_gen: str, products: list) -> None:
    csv_file = next(path_gen)
    writer.save_quotes_to_csv(products, csv_file)


def get_all_products() -> None:
    driver = init_driver()
    path_generator = CSVGenerator.get_csv_path()
    try:
        for url in URLS:
            write_to_csv(path_generator, get_products(driver, url))
    finally:
        driver.quit()


if __name__ == "__main__":
    get_all_products()
