import csv
from dataclasses import dataclass
from urllib.parse import urljoin

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


def _create_driver() -> webdriver.Chrome:
    return webdriver.Chrome()


def _accept_cookies(driver: webdriver.Chrome) -> None:
    try:
        btn = WebDriverWait(driver, 1).until(
            expected_conditions.element_to_be_clickable(
                (By.CLASS_NAME, "acceptCookies"))
        )
        btn.click()
    except TimeoutException:
        pass


def _click_more_until_end(driver: webdriver.Chrome) -> None:
    while True:
        try:
            more_btn = WebDriverWait(driver, 2).until(
                expected_conditions.element_to_be_clickable(
                    (By.CLASS_NAME, "ecomerce-items-scroll-more"))
            )
            driver.execute_script("arguments[0].click();", more_btn)
        except TimeoutException:
            break


def _parse_products(driver: webdriver.Chrome) -> list[Product]:
    products = []

    cards = driver.find_elements(By.CSS_SELECTOR, ".thumbnail")

    for card in cards:
        title = card.find_element(
            By.CSS_SELECTOR, ".title"
        ).get_attribute("title")

        description = card.find_element(
            By.CSS_SELECTOR, ".description"
        ).text

        price = float(
            card.find_element(
                By.CSS_SELECTOR, ".price"
            ).text.replace("$", ""))

        rating = len(
            card.find_elements(
                By.CSS_SELECTOR, ".ratings .ws-icon-star")
        )

        num_of_reviews = int(card.find_element(
            By.CSS_SELECTOR, ".ratings .review-count"
        ).text.split()[0])

        products.append(
            Product(
                title=title,
                description=description,
                price=price,
                rating=rating,
                num_of_reviews=num_of_reviews,
            )
        )

    return products


def _save_to_csv(filename: str, products: list[Product]) -> None:
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            ["title", "description", "price", "rating", "num_of_reviews"]
        )
        for product in products:
            writer.writerow(
                [product.title,
                 product.description,
                 product.price,
                 product.rating,
                 product.num_of_reviews]
            )


def _scrape_page(driver: webdriver.Chrome, url: str, filename: str) -> None:
    driver.get(url)
    _accept_cookies(driver)
    _click_more_until_end(driver)
    products = _parse_products(driver)
    _save_to_csv(filename, products)


def get_all_products() -> None:
    with webdriver.Chrome() as driver:
        pages = {
            "home.csv": HOME_URL,
            "computers.csv": urljoin(HOME_URL, "computers"),
            "laptops.csv": urljoin(HOME_URL, "computers/laptops"),
            "tablets.csv": urljoin(HOME_URL, "computers/tablets"),
            "phones.csv": urljoin(HOME_URL, "phones"),
            "touch.csv": urljoin(HOME_URL, "phones/touch"),
        }
        for filename, url in pages.items():
            _scrape_page(driver, url, filename)


if __name__ == "__main__":
    get_all_products()