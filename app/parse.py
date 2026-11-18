import csv
import os
import re
import time
from dataclasses import dataclass
from typing import List
from urllib.parse import urljoin

from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait
from tqdm import tqdm


BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")

PAGES = {
    "home": "",
    "computers": "computers",
    "laptops": "computers/laptops",
    "tablets": "computers/tablets",
    "phones": "phones",
    "touch": "phones/touch",
}

CARD_SELECTOR = ".thumbnail"
MORE_BUTTON_SELECTOR = ".ecomerce-items-scroll-more"
FIELDNAMES = ["title", "description", "price", "rating", "num_of_reviews"]

WAIT_TIMEOUT = 15
MORE_CLICK_TIMEOUT = 5
MAX_MORE_CLICKS = 200


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


def _create_driver() -> webdriver.Chrome:
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    return webdriver.Chrome(options=options)


def _accept_cookies(driver: webdriver.Chrome) -> None:
    buttons = driver.find_elements(
        By.XPATH, "//button[contains(., 'Accept')]"
    )
    for button in buttons:
        try:
            if button.is_displayed():
                button.click()
                time.sleep(0.5)
                return
        except WebDriverException:
            continue


def _load_all_items(driver: webdriver.Chrome) -> None:
    wait = WebDriverWait(driver, WAIT_TIMEOUT)
    try:
        wait.until(
            ec.presence_of_element_located((By.CSS_SELECTOR, CARD_SELECTOR))
        )
    except TimeoutException:
        return

    for _ in range(MAX_MORE_CLICKS):
        buttons = [
            button
            for button in driver.find_elements(
                By.CSS_SELECTOR, MORE_BUTTON_SELECTOR
            )
            if button.is_displayed()
        ]
        if not buttons:
            return

        items_before = len(
            driver.find_elements(By.CSS_SELECTOR, CARD_SELECTOR)
        )
        buttons[0].click()
        try:
            WebDriverWait(driver, MORE_CLICK_TIMEOUT).until(
                lambda d: len(
                    d.find_elements(By.CSS_SELECTOR, CARD_SELECTOR)
                )
                > items_before
            )
        except TimeoutException:
            return


def _parse_product(card: WebElement) -> Product:
    title_element = card.find_element(By.CSS_SELECTOR, ".title")
    title = title_element.get_attribute("title") or title_element.text.strip()
    description = (
        card.find_element(By.CSS_SELECTOR, ".description")
        .text.strip()
    )
    price_text = card.find_element(By.CSS_SELECTOR, ".price").text
    price = float(price_text.replace("$", "").strip())
    review_count_text = card.find_element(
        By.CSS_SELECTOR, ".ratings .review-count"
    ).text
    num_reviews = int(re.search(r"\d+", review_count_text).group())

    rating_parents = card.find_elements(
        By.CSS_SELECTOR, ".ratings p[data-rating]"
    )
    if rating_parents:
        rating = int(rating_parents[0].get_attribute("data-rating"))
    else:
        rating = len(
            card.find_elements(By.CSS_SELECTOR, ".ratings .ws-icon-star")
        )

    return Product(title, description, price, rating, num_reviews)


def _write_csv(filename: str, products: List[Product]) -> None:
    with open(filename, "w", newline="") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(FIELDNAMES)
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


def _scrape_page(driver: webdriver.Chrome, url: str, filename: str) -> None:
    driver.get(url)
    _accept_cookies(driver)
    _load_all_items(driver)

    cards = driver.find_elements(By.CSS_SELECTOR, CARD_SELECTOR)
    products = [_parse_product(card) for card in cards]
    _write_csv(filename, products)


def get_all_products() -> None:
    driver = _create_driver()
    try:
        for page_name in tqdm(PAGES, desc="Scraping pages"):
            url = urljoin(HOME_URL, PAGES[page_name])
            _scrape_page(driver, url, f"{page_name}.csv")
    finally:
        driver.quit()


if __name__ == "__main__":
    get_all_products()
    print(f"CSV files saved to {os.getcwd()}")
