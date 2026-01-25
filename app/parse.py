from __future__ import annotations

import csv
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Protocol, Tuple
from urllib.parse import urljoin

from selenium import webdriver
from selenium.common.exceptions import (
    ElementClickInterceptedException,
    NoSuchElementException,
    StaleElementReferenceException,
    TimeoutException,
)
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.ui import WebDriverWait


BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


class BookLike(Protocol):
    title: str
    content: str


def _build_driver(headless: bool = True) -> webdriver.Chrome:
    options = Options()
    if headless:
        options.add_argument("--headless=new")

    options.add_argument("--window-size=1400,900")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(options=options)
    driver.implicitly_wait(0)
    return driver


def _wait(
    driver: webdriver.Chrome,
    timeout: float = 10.0,
) -> WebDriverWait:
    return WebDriverWait(driver, timeout)


def _maybe_accept_cookies(
    driver: webdriver.Chrome,
    timeout: float = 2.0,
) -> None:
    """
    Sometimes cookie banner appears and blocks clicks.
    Try to click a visible button containing 'accept' or 'got it'.
    """
    xpath = (
        "//button[contains("
        "translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', "
        "'abcdefghijklmnopqrstuvwxyz'),"
        " 'accept') or contains("
        "translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', "
        "'abcdefghijklmnopqrstuvwxyz'),"
        " 'got it')]"
    )

    try:
        button = _wait(driver, timeout).until(
            expected_conditions.element_to_be_clickable((By.XPATH, xpath))
        )
        button.click()
    except TimeoutException:
        return
    except (ElementClickInterceptedException,
            StaleElementReferenceException):
        return


def _wait_for_products(
    driver: webdriver.Chrome,
    timeout: float = 10.0,
) -> None:
    _wait(driver, timeout).until(
        expected_conditions.presence_of_all_elements_located(
            (By.CSS_SELECTOR, "div.thumbnail")
        )
    )


def _parse_price(text: str) -> float:
    cleaned = text.strip().replace("$", "")
    return float(cleaned)


def _parse_reviews(text: str) -> int:
    match = re.search(r"(\d+)", text)
    if match is None:
        return 0
    return int(match.group(1))


def _parse_product_card(card: WebElement) -> Product:
    title_elem = card.find_element(By.CSS_SELECTOR, "a.title")
    title = title_elem.get_attribute("title").strip()

    description = card.find_element(
        By.CSS_SELECTOR, "p.description"
    ).text.strip()

    price_text = card.find_element(By.CSS_SELECTOR, "h4.price").text
    price = _parse_price(price_text)

    stars = card.find_elements(
        By.CSS_SELECTOR,
        "div.ratings span.glyphicon-star",
    )
    rating = len(stars)

    reviews_text = card.find_element(
        By.CSS_SELECTOR,
        "div.ratings p.pull-right",
    ).text
    num_of_reviews = _parse_reviews(reviews_text)

    return Product(
        title=title,
        description=description,
        price=price,
        rating=rating,
        num_of_reviews=num_of_reviews,
    )


def _collect_products_on_page(driver: webdriver.Chrome) -> List[Product]:
    cards = driver.find_elements(By.CSS_SELECTOR, "div.thumbnail")
    products: List[Product] = []

    for card in cards:
        try:
            product = _parse_product_card(card)
            products.append(product)
        except NoSuchElementException:
            continue
        except StaleElementReferenceException:
            continue

    return products


def _find_more_button(driver: webdriver.Chrome) -> Optional[WebElement]:
    try:
        button = driver.find_element(
            By.XPATH,
            "//a[contains(@class,'btn') and normalize-space()='More']",
        )
    except NoSuchElementException:
        return None

    if not button.is_displayed():
        return None

    return button


def _click_more_until_end(
    driver: webdriver.Chrome,
    timeout: float = 10.0,
) -> None:
    """
    For pages with "More" pagination: click until the button disappears.
    After each click, wait until products count increases.
    """
    while True:
        _maybe_accept_cookies(driver)

        more_button = _find_more_button(driver)
        if more_button is None:
            return

        prev_count = len(driver.find_elements(By.CSS_SELECTOR,
                                              "div.thumbnail"))

        try:
            driver.execute_script(
                "arguments[0].scrollIntoView({block: 'center'});",
                more_button,
            )
            _wait(driver, timeout).until(
                expected_conditions.element_to_be_clickable(more_button)
            )
            more_button.click()
        except (ElementClickInterceptedException,
                StaleElementReferenceException):
            time.sleep(0.5)
            more_button = _find_more_button(driver)
            if more_button is None:
                return
            driver.execute_script("arguments[0].click();", more_button)
        except TimeoutException:
            return

        def count_increased(drv: webdriver.Chrome) -> bool:
            current_count = len(drv.find_elements(By.CSS_SELECTOR,
                                                  "div.thumbnail"))
            no_more = _find_more_button(drv) is None
            return current_count > prev_count or no_more

        try:
            _wait(driver, timeout).until(count_increased)
        except TimeoutException:
            return


def _save_products_to_csv(products: List[Product], filename: str) -> None:
    path = Path(filename)
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(
            ["title", "description", "price", "rating", "num_of_reviews"]
        )
        for product in products:
            writer.writerow(
                [
                    product.title,
                    product.description,
                    f"{product.price:.2f}",
                    product.rating,
                    product.num_of_reviews,
                ]
            )


def _scrape_page(
    driver: webdriver.Chrome,
    url: str,
    out_csv: str,
    use_more_pagination: bool,
) -> None:
    driver.get(url)
    _maybe_accept_cookies(driver)
    _wait_for_products(driver)

    if use_more_pagination:
        _click_more_until_end(driver)

    products = _collect_products_on_page(driver)
    _save_products_to_csv(products, out_csv)


def get_all_products() -> None:
    pages: List[Tuple[str, str, bool]] = [
        ("home.csv", HOME_URL, False),
        ("computers.csv", urljoin(HOME_URL, "computers"), False),
        ("laptops.csv", urljoin(HOME_URL, "computers/laptops"), True),
        ("tablets.csv", urljoin(HOME_URL, "computers/tablets"), True),
        ("phones.csv", urljoin(HOME_URL, "phones"), False),
        ("touch.csv", urljoin(HOME_URL, "phones/touch"), True),
    ]

    driver = _build_driver(headless=True)
    try:
        for out_csv, url, paginate in pages:
            _scrape_page(
                driver=driver,
                url=url,
                out_csv=out_csv,
                use_more_pagination=paginate,
            )
    finally:
        driver.quit()


if __name__ == "__main__":
    get_all_products()