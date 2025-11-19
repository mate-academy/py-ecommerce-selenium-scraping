import csv
import time
from dataclasses import dataclass
from typing import List
from urllib.parse import urljoin

from selenium import webdriver
from selenium.common import TimeoutException
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions


BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")
COMPUTERS_URL = urljoin(HOME_URL, "computers")
PHONES_URL = urljoin(HOME_URL, "phones")

LAPTOPS_URL = urljoin(HOME_URL, "computers/laptops")
TABLETS_URL = urljoin(HOME_URL, "computers/tablets")
TOUCH_URL = urljoin(HOME_URL, "phones/touch")


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


def parse_single_product(product: WebElement) -> Product:
    return Product(
        title=(
            product
            .find_element(By.CLASS_NAME, "title")
            .get_attribute("title")
        ),
        description=product.find_element(By.CLASS_NAME, "description").text,
        price=float(
            product
            .find_element(By.CLASS_NAME, "price")
            .text.replace("$", "")
        ),
        rating=len(product.find_elements(By.CLASS_NAME, "ws-icon-star")),
        num_of_reviews=int(
            product
            .find_element(By.CSS_SELECTOR, '[itemprop="reviewCount"]')
            .text
        ),
    )


def parse_all_product_on_page(driver: WebDriver) -> List[Product]:
    cards = driver.find_elements(By.CSS_SELECTOR, "div.card.thumbnail")
    result = []
    for card in cards:
        product = parse_single_product(card)
        result.append(product)
    return result


def accept_cookies(driver: WebDriver) -> None:
    try:
        button = WebDriverWait(driver, 3).until(
            expected_conditions
            .element_to_be_clickable((By.CSS_SELECTOR, ".acceptCookies"))
        )
        button.click()
        time.sleep(0.2)
    except TimeoutException:
        pass


def click_more_button(driver: WebDriver) -> None:
    wait = WebDriverWait(driver, 10)

    while True:
        try:
            old_count = len(
                driver.find_elements(By.CSS_SELECTOR, "div.card.thumbnail")
            )

            button = wait.until(
                expected_conditions.element_to_be_clickable(
                    (By.CSS_SELECTOR, ".ecomerce-items-scroll-more")
                )
            )

            driver.execute_script("arguments[0].scrollIntoView(true);", button)
            time.sleep(0.2)

            button.click()

            wait.until(
                lambda d: len(
                    d.find_elements(By.CSS_SELECTOR, "div.card.thumbnail")
                )
                > old_count
            )

            time.sleep(0.3)

        except Exception:
            break


def parse_page(
        driver: WebDriver,
        url: str,
        csv_filename: str,
        pagination: bool = False
) -> None:
    driver.get(url)

    accept_cookies(driver)

    if pagination:
        click_more_button(driver)

    products = parse_all_product_on_page(driver)
    save_to_csv(products, csv_filename)


def get_all_products() -> None:
    options = webdriver.ChromeOptions()
    # options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(options=options)

    parse_page(driver, HOME_URL, "home.csv")
    parse_page(driver, COMPUTERS_URL, "computers.csv")
    parse_page(driver, PHONES_URL, "phones.csv")

    parse_page(driver, LAPTOPS_URL, "laptops.csv", pagination=True)
    parse_page(driver, TABLETS_URL, "tablets.csv", pagination=True)
    parse_page(driver, TOUCH_URL, "touch.csv", pagination=True)

    driver.quit()


def save_to_csv(products: List[Product], csv_filename: str) -> None:
    with open(csv_filename, "w", newline="") as file:
        writer = csv.writer(file)
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
                    product.num_of_reviews,
                ]
            )


if __name__ == "__main__":
    get_all_products()
