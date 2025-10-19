import csv
from dataclasses import dataclass, astuple
from selenium.webdriver.support import expected_conditions
from typing import Generator
from urllib.parse import urljoin

from selenium import webdriver
from selenium.common import (
    NoSuchElementException,
    ElementNotInteractableException,
    ElementClickInterceptedException, TimeoutException,
)
from selenium.webdriver.firefox.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.wait import WebDriverWait

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")

urls = {
    "laptops": urljoin(HOME_URL, "computers/laptops"),
    "home": HOME_URL,
    "computers": urljoin(HOME_URL, "computers"),
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


def parse_item(item: WebElement) -> Product:
    title = item.find_element(
        By.CSS_SELECTOR, ".title"
    ).get_attribute("title")

    description = item.find_element(By.CSS_SELECTOR, ".description").text

    try:
        price = float(
            item.find_element(
                By.CSS_SELECTOR, "span[itemprop=price]"
            ).text.replace("$", "")
        )
    except NoSuchElementException:
        try:
            price = float(
                item.find_element(By.CSS_SELECTOR, ".price").text.replace(
                    "$", ""
                )
            )
        except NoSuchElementException:
            price = 0.0

    rating = len(item.find_elements(By.CSS_SELECTOR, ".ws-icon-star"))

    num_of_reviews = int(
        item.find_element(
            By.CSS_SELECTOR,
            "[itemprop=reviewCount]",
        ).text
    )

    return Product(
        title=title,
        description=description,
        price=price,
        rating=rating,
        num_of_reviews=num_of_reviews,
    )


def get_more_anchors(driver: WebDriver) -> Generator[WebElement, None, None]:
    while True:
        try:
            more_anchor = driver.find_element(
                By.CSS_SELECTOR, ".ecomerce-items-scroll-more"
            )
            if (
                more_anchor
                and "display: none;" not in more_anchor.get_attribute("style")
            ):
                yield more_anchor
            else:
                break
        except NoSuchElementException:
            break


def parse_list_page(driver: WebDriver) -> list[Product]:
    for more_anchor in get_more_anchors(driver):
        try:
            more_anchor.click()
        except (
            ElementNotInteractableException,
            ElementClickInterceptedException,
        ):
            pass

    items = driver.find_elements(By.CSS_SELECTOR, ".product-wrapper")

    products = [parse_item(item) for item in items]

    return products


def get_all_products() -> None:
    with webdriver.Firefox() as driver:

        for page, url in urls.items():
            driver.get(url)
            try:
                wait = WebDriverWait(driver, 3)
                accept_cookie_button = wait.until(
                    expected_conditions.element_to_be_clickable(
                        (
                            By.CSS_SELECTOR,
                            ".acceptCookies"
                        )
                    )
                )
                accept_cookie_button.click()
            except (
                    TimeoutException,
                    ElementClickInterceptedException,
                    NoSuchElementException
            ):
                pass

            products = parse_list_page(driver)

            with open(f"{page}.csv", "w", newline="") as result_file:
                writer = csv.writer(result_file)
                writer.writerow(
                    (
                        "title",
                        "description",
                        "price",
                        "rating",
                        "num_of_reviews",
                    )
                )
                for product in products:
                    writer.writerow(astuple(product))


if __name__ == "__main__":
    get_all_products()
