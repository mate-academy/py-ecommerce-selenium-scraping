import csv
import re
import time
from dataclasses import dataclass
from urllib.parse import urljoin
from typing import List, Optional

from selenium import webdriver
from selenium.common.exceptions import (
    ElementClickInterceptedException,
    NoSuchElementException,
    StaleElementReferenceException,
    TimeoutException,
    InvalidSelectorException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as ec
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


def _create_driver() -> webdriver.Chrome:
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    driver = webdriver.Chrome(options=options)
    driver.set_page_load_timeout(30)
    return driver


def _scrape_page(driver: webdriver.Chrome, url: str) -> List[Product]:
    driver.get(url)
    _try_accept_cookies(driver)

    WebDriverWait(driver, 15).until(
        ec.presence_of_element_located((By.CSS_SELECTOR, "a.title"))
    )

    _click_load_more_until_end(driver)
    return _parse_products(driver)


def _try_accept_cookies(driver: webdriver.Chrome) -> None:
    fallback_xpath = (
        "//button[contains(., 'Accept') or contains(., 'I agree')]"
    )
    selectors = [
        (By.ID, "CybotCookiebotDialogBodyLevelButtonAccept"),
        (By.ID, "CybotCookiebotDialogBodyButtonAccept"),
        (By.ID, "onetrust-accept-btn-handler"),
        (By.CSS_SELECTOR, "button[aria-label='Accept']"),
        (By.XPATH, fallback_xpath),
    ]
    for by, selector in selectors:
        try:
            button = WebDriverWait(driver, 2).until(
                ec.element_to_be_clickable((by, selector))
            )
            button.click()
            return
        except (TimeoutException, InvalidSelectorException):
            continue
        except (
            ElementClickInterceptedException,
            StaleElementReferenceException,
            InvalidSelectorException,
        ):
            try:
                driver.execute_script("arguments[0].click();", button)
                return
            except Exception:
                continue


def _click_load_more_until_end(driver: webdriver.Chrome) -> None:
    while True:
        _try_accept_cookies(driver)
        more_button = _find_more_button(driver)
        if more_button is None:
            return

        old_count = len(driver.find_elements(By.CSS_SELECTOR, "a.title"))
        driver.execute_script(
            "arguments[0].scrollIntoView({block: 'center'});", more_button
        )

        try:
            more_button.click()
        except (
            ElementClickInterceptedException,
            StaleElementReferenceException,
        ):
            driver.execute_script("arguments[0].click();", more_button)

        time.sleep(0.2)
        try:
            WebDriverWait(driver, 10).until(
                lambda d: len(d.find_elements(By.CSS_SELECTOR, "a.title"))
                > old_count
            )
        except TimeoutException:
            return


def _find_more_button(driver: webdriver.Chrome) -> Optional[WebElement]:
    selectors = [
        (By.CSS_SELECTOR, "a.ecomerce-items-scroll-more"),
        (By.CSS_SELECTOR, "button.ecomerce-items-scroll-more"),
        (By.CSS_SELECTOR, "#more"),
        (
            By.XPATH,
            "//a[contains(@class,'ecomerce-items-scroll-more') and "
            "not(contains(@class,'disabled'))]",
        ),
        (
            By.XPATH,
            "//button[contains(@class,'ecomerce-items-scroll-more') and "
            "not(@disabled)]",
        ),
    ]
    for by, selector in selectors:
        try:
            btn = driver.find_element(by, selector)
            if btn.is_displayed() and btn.is_enabled():
                return btn
        except (NoSuchElementException, InvalidSelectorException):
            continue
    return None


def _parse_products(driver: webdriver.Chrome) -> List[Product]:
    product_cards = driver.find_elements(
        By.XPATH,
        "//div[contains(@class,'thumbnail') and "
        ".//a[contains(@class,'title')]]",
    )

    if not product_cards:
        product_cards = driver.find_elements(
            By.CSS_SELECTOR,
            "div.product-wrapper",
        )

    if not product_cards:
        product_cards = driver.find_elements(
            By.XPATH,
            "//div[.//a[contains(@class,'title')] and "
            ".//h4[contains(@class,'price')]]",
        )

    products: List[Product] = []
    for card in product_cards:
        title_el = card.find_element(By.CSS_SELECTOR, "a.title")
        title = title_el.get_attribute("title") or title_el.text
        description = card.find_element(By.CSS_SELECTOR, "p.description").text

        price_text = card.find_element(By.CSS_SELECTOR, "h4.price").text
        price = float(price_text.replace("$", "").strip())

        rating = _parse_rating(card)
        reviews = _parse_reviews(card)

        products.append(
            Product(
                title=title.strip(),
                description=description.strip(),
                price=price,
                rating=rating,
                num_of_reviews=reviews,
            )
        )
    return products


def _parse_rating(card: WebElement) -> int:
    stars = card.find_elements(
        By.CSS_SELECTOR,
        "div.ratings span.glyphicon-star",
    )
    if stars:
        return len(stars)

    stars = card.find_elements(
        By.XPATH,
        ".//*[contains(@class,'star') and not(contains(@class,'empty'))]",
    )
    return len(stars)


def _parse_reviews(card: WebElement) -> int:
    candidates = [
        (By.CSS_SELECTOR, "div.ratings p.pull-right"),
        (By.CSS_SELECTOR, "div.ratings p.review-count"),
    ]
    text = ""
    for by, selector in candidates:
        try:
            text = card.find_element(by, selector).text
            break
        except NoSuchElementException:
            continue
    match = re.search(r"\d+", text)
    return int(match.group(0)) if match else 0


def _write_products(page_name: str, products: List[Product]) -> None:
    with open(f"{page_name}.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            ["title", "description", "price", "rating", "num_of_reviews"]
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


def get_all_products() -> None:
    pages = {
        "home": HOME_URL,
        "computers": urljoin(HOME_URL, "computers"),
        "laptops": urljoin(HOME_URL, "computers/laptops"),
        "tablets": urljoin(HOME_URL, "computers/tablets"),
        "phones": urljoin(HOME_URL, "phones"),
        "touch": urljoin(HOME_URL, "phones/touch"),
    }

    driver = _create_driver()
    try:
        for page_name, page_url in pages.items():
            products = _scrape_page(driver, page_url)
            _write_products(page_name, products)
    finally:
        driver.quit()


if __name__ == "__main__":
    get_all_products()
