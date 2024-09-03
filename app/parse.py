import csv
from dataclasses import dataclass
from urllib.parse import urljoin

from bs4 import BeautifulSoup, Tag
from selenium import webdriver
from selenium.common import (
    TimeoutException,
    NoSuchElementException,
    ElementNotInteractableException
)
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")

CATEGORIES = {
    "home": HOME_URL,
    "computers": urljoin(HOME_URL, "computers/"),
    "phones": urljoin(HOME_URL, "phones/"),
    "laptops": urljoin(HOME_URL, "computers/laptops"),
    "tablets": urljoin(HOME_URL, "computers/tablets"),
    "touch": urljoin(HOME_URL, "phones/touch")
}


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


def parse_single_product(tag: Tag) -> Product | None:
    try:
        title = tag.select_one(".title")["title"]
        description = tag.select_one(".description").get_text(
            strip=True
        ).replace("\xa0", " ")
        price = float(tag.select_one(".price").get_text(
            strip=True
        ).replace("$", ""))
        rating = len(tag.select("p > .ws-icon-star"))
        num_of_reviews = int(tag.select_one(".review-count").get_text(
            strip=True
        ).split()[0])
    except (AttributeError, TypeError, ValueError) as error:
        print(f"Error parsing product: {error}")
        return None

    return Product(title, description, price, rating, num_of_reviews)


def parse_product_page(page_soup: BeautifulSoup) -> list[Product]:
    products = page_soup.select(".thumbnail")
    return [
        parse_single_product(product)
        for product in products if parse_single_product(product)
    ]


def accept_cookies(driver: webdriver.Chrome) -> None:
    try:
        cookie_button = WebDriverWait(driver, 10).until(
            expected_conditions.presence_of_element_located(
                (By.CLASS_NAME, "acceptCookies")
            )
        )
        cookie_button.click()
    except (NoSuchElementException, TimeoutException):
        pass


def load_whole_page(driver: webdriver.Chrome) -> None:
    while True:
        try:
            button = WebDriverWait(driver, 3).until(
                expected_conditions.element_to_be_clickable(
                    (By.CSS_SELECTOR, "a.ecomerce-items-scroll-more")
                )
            )
            button.click()
            WebDriverWait(driver, 3).until(
                expected_conditions.presence_of_element_located(
                    (By.CSS_SELECTOR, ".thumbnail")
                )
            )
        except (
                NoSuchElementException,
                TimeoutException,
                ElementNotInteractableException
        ):
            break


def scrape_products(
        driver: webdriver.Chrome,
        url: str
) -> list[Product]:
    driver.get(url)

    load_whole_page(driver)

    page_soup = BeautifulSoup(driver.page_source, "html.parser")
    return parse_product_page(page_soup)


def write_products_to_csv(
        products: list[Product],
        output_csv_path: str
) -> None:
    with open(
            output_csv_path, mode="w", newline="", encoding="utf-8"
    ) as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(
            [
                "title",
                "description",
                "price",
                "rating",
                "num_of_reviews"
            ]
        )
        for product in products:
            writer.writerow(
                [
                    product.title,
                    product.description,
                    product.price,
                    product.rating,
                    product.num_of_reviews
                ]
            )


def get_all_products() -> None:
    options = Options()
    options.add_argument("--headless")
    driver = webdriver.Chrome(options=options)

    try:
        driver.get(HOME_URL)
        accept_cookies(driver)

        for category, url in CATEGORIES.items():
            products = scrape_products(driver, url)
            write_products_to_csv(products, f"{category}.csv")
    finally:
        driver.quit()


if __name__ == "__main__":
    get_all_products()
