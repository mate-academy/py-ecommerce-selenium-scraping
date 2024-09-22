import csv
import logging
import time
from dataclasses import dataclass

from selenium.webdriver.support import expected_conditions as exp_cond
from urllib.parse import urljoin

from bs4 import BeautifulSoup, Tag
from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.wait import WebDriverWait
from selenium.common.exceptions import (
    TimeoutException,
    ElementClickInterceptedException,
    NoSuchElementException,
)


BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")
COMPUTERS_URL = urljoin(HOME_URL, "computers/")
LAPTOPS_URL = urljoin(HOME_URL, "computers/laptops")
TABLETS_URL = urljoin(HOME_URL, "computers/tablets")
PHONES_URL = urljoin(HOME_URL, "phones/")
TOUCH_URL = urljoin(HOME_URL, "phones/touch")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


_web_driver: WebDriver | None = None


def get_driver() -> WebDriver:
    return _web_driver


def set_driver(new_driver: WebDriver) -> None:
    global _web_driver
    _web_driver = new_driver


def parse_single_product(product_soup: Tag) -> Product:
    return Product(
        title=product_soup.select_one(".caption .title")["title"],
        description=product_soup.select_one(
            ".caption .description"
        ).text,
        price=float(
            product_soup.select_one(
                ".caption .price"
            ).text.replace("$", "")
        ),
        rating=len(
            product_soup.find("div", {"class": "ratings"})
            .find_all("p")[1].find_all("span")
        ),
        num_of_reviews=int(
            product_soup.select_one(
                ".ratings .review-count").text.split(" ")[0]
        )
    )


def click_accept_button(url: str) -> None:
    driver = get_driver()
    driver.get(url)

    try:
        accept_button = WebDriverWait(driver, 2).until(
            exp_cond.element_to_be_clickable((By.CLASS_NAME, "acceptCookies"))
        )
        accept_button.click()
    except Exception as e:
        print(f"Accept cookies button not found: {e}")


def get_information_from_product_page(url: str) -> [Product]:
    driver = get_driver()
    driver.get(url)

    while True:
        try:
            more_button = WebDriverWait(driver, 2).until(
                exp_cond.visibility_of_element_located(
                    (By.CSS_SELECTOR, "a.ecomerce-items-scroll-more"))
            )

            if more_button.is_enabled():
                actions = ActionChains(driver)
                actions.move_to_element(more_button).perform()
                more_button.click()
                time.sleep(0.5)

                WebDriverWait(driver, 5).until(
                    exp_cond.presence_of_element_located(
                        (By.CSS_SELECTOR, ".product-wrapper.card-body")
                    )
                )
            else:
                logger.info("'Load More' button is no longer available.")
                break

        except (TimeoutException, NoSuchElementException):
            logger.warning("'Load More' button not found or unavailable.")
            break
        except ElementClickInterceptedException:
            logger.warning(
                "Failed to click the 'Load More' button. Retrying."
            )

    soup = BeautifulSoup(driver.page_source, "html.parser")
    products = soup.select(".product-wrapper.card-body")

    return [parse_single_product(product) for product in products]


def sanitize_description(description: str) -> str:
    return description.replace("\xa0", " ")


def write_products_to_csv(path_to_csv_file: str, products: [Product]) -> None:
    with open(path_to_csv_file, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(
            [
                "title", "description", "price",
                "rating", "num_of_reviews",
            ]
        )
        for product in products:
            writer.writerow(
                [
                    product.title,
                    sanitize_description(product.description),
                    product.price,
                    product.rating,
                    product.num_of_reviews,
                ]
            )


urls_and_files = [
    (HOME_URL, "home.csv"),
    (COMPUTERS_URL, "computers.csv"),
    (LAPTOPS_URL, "laptops.csv"),
    (TABLETS_URL, "tablets.csv"),
    (PHONES_URL, "phones.csv"),
    (TOUCH_URL, "touch.csv"),
]


def get_all_products() -> None:
    with webdriver.Chrome() as new_driver:
        set_driver(new_driver)
        click_accept_button(HOME_URL)
        for url, path in urls_and_files:
            products = get_information_from_product_page(url)
            write_products_to_csv(path, products)


if __name__ == "__main__":
    get_all_products()
