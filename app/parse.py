import csv
from dataclasses import dataclass, fields
from pathlib import Path
from typing import List
from urllib.parse import urljoin

from selenium import webdriver
from selenium.common.exceptions import (
    ElementClickInterceptedException,
    NoSuchElementException,
    StaleElementReferenceException,
    TimeoutException,
)
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait
from tqdm import tqdm

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")

LOCAL_CHROME = (
    Path(__file__).resolve().parent.parent
    / ".chrome"
    / "chrome-linux64"
    / "chrome"
)

PAGES = {
    "home": HOME_URL,
    "computers": urljoin(HOME_URL, "computers"),
    "laptops": urljoin(HOME_URL, "computers/laptops"),
    "tablets": urljoin(HOME_URL, "computers/tablets"),
    "phones": urljoin(HOME_URL, "phones"),
    "touch": urljoin(HOME_URL, "phones/touch"),
}

MORE_BUTTON_SELECTOR = ".ecomerce-items-scroll-more"
PRODUCT_SELECTOR = ".thumbnail"
COOKIE_SELECTORS = (
    ".t-acceptAllButton",
    ".acceptCookies",
    "#closeCookieBanner",
    ".cookies > button",
)


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


def create_driver() -> WebDriver:
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    if LOCAL_CHROME.exists():
        options.binary_location = str(LOCAL_CHROME)
    return webdriver.Chrome(options=options)


def accept_cookies(driver: WebDriver) -> None:
    for selector in COOKIE_SELECTORS:
        try:
            button = WebDriverWait(driver, 3).until(
                ec.element_to_be_clickable((By.CSS_SELECTOR, selector))
            )
            button.click()
            return
        except (TimeoutException, ElementClickInterceptedException):
            continue


def _count_products(driver: WebDriver) -> int:
    return len(driver.find_elements(By.CSS_SELECTOR, PRODUCT_SELECTOR))


def _is_more_button_available(driver: WebDriver) -> bool:
    buttons = driver.find_elements(By.CSS_SELECTOR, MORE_BUTTON_SELECTOR)
    if not buttons:
        return False
    button = buttons[0]
    if not button.is_displayed():
        return False
    classes = button.get_attribute("class") or ""
    return "disabled" not in classes.split()


def _click_more_button(driver: WebDriver) -> bool:
    try:
        button = driver.find_element(By.CSS_SELECTOR, MORE_BUTTON_SELECTOR)
    except NoSuchElementException:
        return False
    try:
        button.click()
    except ElementClickInterceptedException:
        accept_cookies(driver)
        try:
            button.click()
        except (
            ElementClickInterceptedException,
            StaleElementReferenceException,
        ):
            try:
                button = driver.find_element(
                    By.CSS_SELECTOR, MORE_BUTTON_SELECTOR
                )
            except NoSuchElementException:
                return False
            driver.execute_script("arguments[0].click();", button)
    except StaleElementReferenceException:
        return False
    return True


def load_all_products(driver: WebDriver) -> None:
    while _is_more_button_available(driver):
        current_count = _count_products(driver)
        if not _click_more_button(driver):
            break
        try:
            WebDriverWait(driver, 10).until(
                lambda d: _count_products(d) > current_count
            )
        except TimeoutException:
            if not _is_more_button_available(driver):
                break
            raise


def _parse_product(card: WebElement) -> Product:
    title_element = card.find_element(By.CSS_SELECTOR, ".title")
    title = title_element.get_attribute("title") or title_element.text
    description = card.find_element(
        By.CSS_SELECTOR, ".description"
    ).text
    price_text = card.find_element(By.CSS_SELECTOR, ".price").text
    price = float(
        price_text.replace("$", "").replace(",", "").strip()
    )
    rating_elements = card.find_elements(By.CSS_SELECTOR, "[data-rating]")
    if rating_elements:
        rating = int(rating_elements[0].get_attribute("data-rating"))
    else:
        rating = len(
            card.find_elements(By.CSS_SELECTOR, ".ws-icon-star")
        )
    reviews_text = card.find_element(
        By.CSS_SELECTOR, ".ratings .pull-right"
    ).text
    num_of_reviews = int(reviews_text.split()[0])
    return Product(
        title=title,
        description=description,
        price=price,
        rating=rating,
        num_of_reviews=num_of_reviews,
    )


def parse_products(driver: WebDriver) -> List[Product]:
    cards = driver.find_elements(By.CSS_SELECTOR, PRODUCT_SELECTOR)
    return [_parse_product(card) for card in cards]


def save_products(products: List[Product], page_name: str) -> None:
    field_names = [field.name for field in fields(Product)]
    with open(f"{page_name}.csv", "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(field_names)
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


def scrape_page(driver: WebDriver, url: str) -> List[Product]:
    driver.get(url)
    accept_cookies(driver)
    load_all_products(driver)
    return parse_products(driver)


def get_all_products() -> None:
    driver = create_driver()
    try:
        for page_name, url in tqdm(PAGES.items(), desc="Pages"):
            products = scrape_page(driver, url)
            save_products(products, page_name)
    finally:
        driver.quit()


if __name__ == "__main__":
    get_all_products()
