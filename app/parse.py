from dataclasses import dataclass
import csv
import re
from urllib.parse import urljoin

from selenium import webdriver
from selenium.common.exceptions import (
    ElementClickInterceptedException,
    TimeoutException,
)
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait


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
WAIT_TIME = 10


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


def normalize_text(value: str) -> str:
    return value.replace("\xa0", " ")


def get_driver() -> WebDriver:
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")

    return webdriver.Chrome(options=options)


def accept_cookies(driver: WebDriver) -> None:
    selectors = [
        "button[data-testid='uc-accept-all-button']",
        "button#onetrust-accept-btn-handler",
        "button[aria-label='Accept cookies']",
    ]

    for selector in selectors:
        buttons = driver.find_elements(By.CSS_SELECTOR, selector)

        if buttons:
            buttons[0].click()
            return

    buttons = driver.find_elements(
        By.XPATH,
        "//button[contains(., 'Accept') or contains(., 'accept')]",
    )

    if buttons:
        buttons[0].click()


def load_all_products(driver: WebDriver) -> None:
    wait = WebDriverWait(driver, WAIT_TIME)
    wait.until(ec.presence_of_element_located((By.CSS_SELECTOR, ".thumbnail")))

    while True:
        buttons = driver.find_elements(
            By.CSS_SELECTOR,
            ".ecomerce-items-scroll-more",
        )

        if not buttons or not buttons[0].is_displayed():
            return

        current_count = len(get_product_cards(driver))
        driver.execute_script("arguments[0].scrollIntoView();", buttons[0])

        try:
            buttons[0].click()
        except ElementClickInterceptedException:
            driver.execute_script("arguments[0].click();", buttons[0])

        try:
            wait.until(
                lambda browser: len(get_product_cards(browser)) > current_count
            )
        except TimeoutException:
            if not buttons[0].is_displayed():
                return


def get_product_cards(driver: WebDriver) -> list[WebElement]:
    return driver.find_elements(By.CSS_SELECTOR, ".thumbnail")


def parse_price(card: WebElement) -> float:
    price = card.find_element(By.CSS_SELECTOR, ".price").text
    return float(price.replace("$", ""))


def parse_rating(card: WebElement) -> int:
    return len(card.find_elements(By.CSS_SELECTOR, ".ratings .ws-icon-star"))


def parse_num_of_reviews(card: WebElement) -> int:
    review_count = card.find_element(By.CSS_SELECTOR, ".review-count").text
    match = re.search(r"\d+", review_count)

    if match is None:
        return 0

    return int(match.group())


def parse_product_card(card: WebElement) -> Product:
    title = card.find_element(By.CSS_SELECTOR, ".title").get_attribute("title")

    if title is None:
        title = card.find_element(By.CSS_SELECTOR, ".title").text

    return Product(
        title=normalize_text(title),
        description=normalize_text(
            card.find_element(By.CSS_SELECTOR, ".description").text
        ),
        price=parse_price(card),
        rating=parse_rating(card),
        num_of_reviews=parse_num_of_reviews(card),
    )


def parse_products(driver: WebDriver, url: str) -> list[Product]:
    driver.get(url)
    accept_cookies(driver)
    load_all_products(driver)

    return [
        parse_product_card(card)
        for card in get_product_cards(driver)
    ]


def write_products_to_csv(path: str, products: list[Product]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(
            [
                "title",
                "description",
                "price",
                "rating",
                "num_of_reviews",
            ]
        )
        writer.writerows(
            [
                product.title,
                product.description,
                product.price,
                product.rating,
                product.num_of_reviews,
            ]
            for product in products
        )


def get_all_products() -> None:
    driver = get_driver()

    try:
        for page_name, url in PAGES.items():
            write_products_to_csv(
                f"{page_name}.csv",
                parse_products(driver, url),
            )
    finally:
        driver.quit()


if __name__ == "__main__":
    get_all_products()
