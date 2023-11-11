import csv
import time
from dataclasses import dataclass
from urllib.parse import urljoin

from selenium import webdriver
from selenium.common import NoSuchElementException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

from tqdm import tqdm


BASE_URL = "https://webscraper.io/"
HOME_PAGE = urljoin(BASE_URL, "test-sites/e-commerce/more")


_driver: WebDriver | None = None


PAGES = {
    "home": HOME_PAGE,
    "computers": urljoin(BASE_URL, "test-sites/e-commerce/more/computers"),
    "laptops": urljoin(
        BASE_URL, "test-sites/e-commerce/more/computers/laptops"
    ),
    "tablets": urljoin(
        BASE_URL, "test-sites/e-commerce/more/computers/tablets"
    ),
    "phones": urljoin(BASE_URL, "test-sites/e-commerce/more/phones"),
    "touch": urljoin(BASE_URL, "test-sites/e-commerce/more/phones/touch"),
}


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


def get_driver() -> WebDriver:
    return _driver


def set_driver(new_driver: WebDriver) -> None:
    global _driver
    _driver = new_driver


def accept_cookies(driver: WebDriver) -> None:
    accept_cookie = driver.find_element(By.ID, "cookieBanner")
    cookie_access = accept_cookie.find_element(
        By.CLASS_NAME, "acceptContainer"
    )

    cookie_access.click()


def press_button_more(driver: WebDriver) -> None:
    while True:
        try:
            btn_more = driver.find_element(
                By.CLASS_NAME, "ecomerce-items-scroll-more"
            )
        except NoSuchElementException:
            break
        else:
            if btn_more.get_attribute("style"):
                break
            btn_more.click()
            time.sleep(0.3)


def parse_products(driver: WebDriver) -> list[Product]:
    card_bodies = driver.find_elements(By.CLASS_NAME, "card-body")

    products = []

    for card_body in tqdm(card_bodies):
        products.append(
            Product(
                title=card_body.find_element(
                    By.CLASS_NAME, "title"
                ).get_attribute(
                    "title"
                ),
                description=card_body.find_element(
                    By.CLASS_NAME, "description"
                ).text,
                price=float(
                    card_body.find_element(
                        By.CLASS_NAME, "price"
                    ).text.replace("$", "")
                ),
                rating=len(
                    card_body.find_elements(
                        By.CLASS_NAME, "ws-icon.ws-icon-star"
                    )
                ),
                num_of_reviews=int(
                    card_body.find_element(
                        By.CLASS_NAME, "review-count"
                    ).text.split()[0]
                ),
            )
        )
    return products


def write_products_to_csv(file_path: str, products: list[Product]) -> None:
    with open(file_path, "w", newline="", encoding="utf-8") as file:
        written = csv.writer(file)
        written.writerow(
            ["title", "description", "price", "rating", "num_of_reviews"]
        )
        for product in products:
            written.writerow(
                [
                    product.title,
                    product.description,
                    product.price,
                    product.rating,
                    product.num_of_reviews,
                ]
            )


def get_all_products() -> None:
    chrome_options = Options()
    chrome_options.add_argument("--headless")

    with webdriver.Chrome(options=chrome_options) as new_driver:
        for name, path in PAGES.items():
            set_driver(new_driver)
            driver = get_driver()
            driver.get(path)
            if name == "home":
                accept_cookies(driver)
            press_button_more(driver)
            products = parse_products(driver)
            write_products_to_csv(file_path=f"{name}.csv", products=products)


if __name__ == "__main__":
    get_all_products()
