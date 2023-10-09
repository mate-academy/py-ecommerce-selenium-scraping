import csv
import logging
import sys
from dataclasses import dataclass, fields, astuple
from urllib.parse import urljoin

from bs4 import BeautifulSoup, Tag
from selenium import webdriver
from selenium.common import NoSuchElementException
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")
URLS = [
    [HOME_URL, "home.csv"],
    [HOME_URL + "computers", "computers.csv"],
    [HOME_URL + "phones", "phones.csv"],
    [HOME_URL + "computers/laptops", "laptops.csv"],
    [HOME_URL + "computers/tablets", "tablets.csv"],
    [HOME_URL + "phones/touch", "touch.csv"]
]


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


PRODUCTS = [field.name for field in fields(Product)]

logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)8s]: %(message)s",
    handlers=[
        logging.FileHandler("parser.log"),
        logging.StreamHandler(sys.stdout),
    ],
)


def initialize_driver() -> WebDriver:
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    driver = webdriver.Chrome(
        service=ChromeService(ChromeDriverManager().install()),
        options=options
    )
    return driver


def accept_cookies(driver: WebDriver) -> None:
    try:
        cookies = WebDriverWait(driver, 5).until(
            expected_conditions.element_to_be_clickable(
                (By.CLASS_NAME, "acceptCookies")
            )
        )
        cookies.click()
    except NoSuchElementException:
        pass


def parse_single_product(soup: Tag) -> [Product]:
    price_str = soup.select_one(".price").text.strip()
    price_str = price_str.replace("$", "").replace(",", "")
    price = float(price_str)

    reviews_elements = soup.select(".review-count")
    first_review_element = reviews_elements[0]
    num_of_reviews_text = first_review_element.text.strip().split()[0]
    num_of_reviews = int(num_of_reviews_text)

    return Product(
        title=soup.select_one(".title")["title"],
        description=soup.select_one(".description").text.replace(" ", " "),
        price=price,
        rating=len(soup.select(".ws-icon.ws-icon-star")),
        num_of_reviews=num_of_reviews,
    )


def more_button(url: str) -> BeautifulSoup:
    driver = initialize_driver()
    driver.get(url)
    accept_cookies(driver)

    try:
        more = driver.find_element(By.CLASS_NAME, "ecomerce-items-scroll-more")

        while more and more.is_displayed():
            more.click()
    except NoSuchElementException:
        pass

    finally:
        return BeautifulSoup(driver.page_source, "html.parser")


def scrape_page(url: str) -> list[Product]:
    soup = more_button(url)
    products_info = soup.select(".thumbnail")
    return [parse_single_product(product) for product in products_info]


def write_product_to_csv(products: list[Product], path: str) -> None:
    with open(path, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(PRODUCTS)
        writer.writerows(astuple(product) for product in products)


def get_all_products() -> None:
    for url, path in URLS:
        products = scrape_page(url)
        write_product_to_csv(products, path)


if __name__ == "__main__":
    get_all_products()
