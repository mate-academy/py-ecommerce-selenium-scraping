import csv
import logging
import time
import random
from tqdm import tqdm
from dataclasses import dataclass, fields, astuple

from selenium.common import (
    WebDriverException,
    TimeoutException,
    NoSuchElementException
)
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.by import By

from app.driver_config import WebDriverConfig
from app import urls
from app.logging_config import setup_logging


setup_logging()


@dataclass
class Product:
    title: str = None
    description: str = None
    price: float = None
    rating: int = None
    num_of_reviews: int = None


def crawling_page(driver: WebDriver, current_url: str) -> None:
    """
    Click Accept Cookies, if need
    Scroll down page and press MORE button if it exists
    """
    try:
        driver.get(current_url)
        wait = WebDriverWait(driver=driver, timeout=2)
        logging.info(f"Open {current_url} page")

        try:
            cookie_button = wait.until(
                ec.element_to_be_clickable(
                    (By.CSS_SELECTOR, "button.acceptCookies")
                )
            )
            cookie_button.click()
            logging.info("Clicked accept cookies button.")
            time.sleep(0.5)
        except (TimeoutException, NoSuchElementException):
            logging.warning("No cookies button or timeout.")

        while True:
            try:
                more_button = wait.until(
                    ec.presence_of_element_located(
                        (By.CSS_SELECTOR,
                         "div.test-site a.ecomerce-items-scroll-more")
                    )
                )
                driver.execute_script(
                    "arguments[0].scrollIntoView({block: 'center'});",
                    more_button
                )
                time.sleep(0.5)

                more_button.click()
                logging.info("Pressed the 'More' button")
                time.sleep(0.1)

            except WebDriverException:
                logging.info("No more 'More' button found. Exiting loop.")
                break

    except WebDriverException as e:
        logging.error(f"Failed to open home page: {e}")

    return None


def get_product_cards(driver: WebDriver) -> list[Product]:
    products: list[Product] = []
    try:
        logging.info("Start: Gathering all product cards")
        product_cards = WebDriverWait(driver=driver, timeout=1).until(
            ec.presence_of_all_elements_located(
                (By.CSS_SELECTOR, "div.product-wrapper.card-body")
            )
        )

        for card in tqdm(
                product_cards,
                desc="Parsing product card."
        ):
            logging.info("Receive product detailed info")
            title = card.find_element(
                By.CSS_SELECTOR, "h4 a.title"
            ).get_property("title")
            description = card.find_element(
                By.CSS_SELECTOR, "p.card-text.description"
            ).text
            price = float(card.find_element(
                By.CSS_SELECTOR, "h4.price"
            ).text.replace("$", ""))
            rating = len(card.find_elements(
                By.CLASS_NAME, "ws-icon-star"
            ))
            num_of_reviews = int(card.find_element(
                By.CSS_SELECTOR, "p.review-count"
            ).text.split()[0])

            products.append(Product(
                title=title,
                description=description,
                price=price,
                rating=rating,
                num_of_reviews=num_of_reviews
            ))

    except (TimeoutException, NoSuchElementException):
        logging.info("Failed: Gathering all product cards")

    logging.info("Stop: Gathering all product cards")
    return products


def write_to_csv(products: list[Product], filename: str) -> None:
    field_titles = [field.name for field in fields(Product)]
    with open(f"{filename}.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(field_titles)
        for product in [astuple(product) for product in products]:
            writer.writerow(product)


def get_all_products() -> None:
    driver_config = WebDriverConfig(headless=True)
    driver = driver_config.set_driver()

    for url, name in tqdm(
            urls.get_urls().items(),
            desc="Parsing pages",
            unit="product"
    ):
        crawling_page(driver, url)
        products = get_product_cards(driver)

        result = []
        if url in [urls.HOME, urls.PHONES, urls.COMPUTERS]:
            for i in random.sample(range(0, len(products)),
                                   min(3, len(products))):
                result.append(products[i])

        else:
            result = products

        write_to_csv(result, name.lower())

    driver_config.quit_driver()


if __name__ == "__main__":
    get_all_products()
