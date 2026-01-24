from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urljoin
import csv
import re
import time
from typing import Iterable, List

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import (
    NoSuchElementException,
    TimeoutException,
    StaleElementReferenceException,
)
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


# ---------- Selenium helpers ----------

def _create_driver(headless: bool = True) -> webdriver.Chrome:
    opts = Options()
    if headless:
        opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--window-size=1360,900")
    # трохи чемності
    opts.add_argument(
        "user-agent=Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0 Safari/537.36"
    )
    return webdriver.Chrome(options=opts)


def _accept_cookies_if_present(driver: webdriver.Chrome) -> None:
    # На сайті інколи з’являється банер — пробуємо натиснути, якщо він є.
    candidates = [
        (By.XPATH, "//button[contains(., 'Accept')]"),
        (By.XPATH, "//button[contains(., 'accept')]"),
        (By.XPATH, "//button[contains(., 'I agree')]"),
        (By.XPATH, "//button[contains(., 'Close')]"),
        (By.CSS_SELECTOR, "button.cookie"),  # на всяк випадок
    ]
    for by, sel in candidates:
        try:
            btn = WebDriverWait(driver, 2).until(
                EC.element_to_be_clickable((by, sel))
            )
            btn.click()
            break
        except TimeoutException:
            continue
        except Exception:
            continue


def _wait_products_present(driver: webdriver.Chrome, timeout: int = 10) -> None:
    WebDriverWait(driver, timeout).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".thumbnail"))
    )


def _click_more_until_exhausted(driver: webdriver.Chrome) -> None:
    """
    Для сторінок із довантаженням (“More” кнопка) натискаємо доки є що грузити.
    Якщо кнопки немає — тихо виходимо.
    """
    while True:
        try:
            # кнопка "More" зазвичай <a class="btn btn-primary btn-lg btn-block">
            more_btn = WebDriverWait(driver, 2).until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//a[contains(., 'More')]")
                )
            )
        except TimeoutException:
            # кнопка відсутня — кінець пагінації
            return

        # щоби не схибити з очікуванням, запам’ятаємо к-сть карток до кліку
        before = len(driver.find_elements(By.CSS_SELECTOR, ".thumbnail"))
        more_btn.click()

        # чекаємо, поки кількість елементів виросте (або таймаут)
        try:
            WebDriverWait(driver, 8).until(
                lambda d: len(d.find_elements(By.CSS_SELECTOR, ".thumbnail")) > before
            )
        except TimeoutException:
            # якщо не зросло — вважаємо, що все завантажили
            return
        # невелика пауза для стабільності
        time.sleep(0.2)


# ---------- Parsing helpers ----------

_PRICE_RE = re.compile(r"[\d.]+")
_REVIEWS_RE = re.compile(r"(\d+)")


def _parse_price(text: str) -> float:
    # типово тексти як "$699.99"
    match = _PRICE_RE.search(text.replace(",", "."))
    return float(match.group(0)) if match else 0.0


def _parse_reviews(text: str) -> int:
    # типово: "14 reviews"
    match = _REVIEWS_RE.search(text)
    return int(match.group(1)) if match else 0


def _extract_products(driver: webdriver.Chrome) -> List[Product]:
    cards = driver.find_elements(By.CSS_SELECTOR, ".thumbnail")
    products: List[Product] = []

    for card in cards:
        try:
            # title
            title_el = card.find_element(By.CSS_SELECTOR, ".title")
            # у демо-сайті текст часто в атрибуті title
            title_text = title_el.get_attribute("title") or title_el.text.strip()

            # description
            desc_el = card.find_element(By.CSS_SELECTOR, ".description")
            desc_text = desc_el.text.strip()

            # price
            price_el = card.find_element(By.CSS_SELECTOR, ".price")
            price_val = _parse_price(price_el.text)

            # rating = кількість зірочок .glyphicon-star
            stars = card.find_elements(
                By.CSS_SELECTOR, ".ratings span.glyphicon.glyphicon-star"
            )
            rating_val = len(stars)

            # reviews
            # інколи це: .ratings p.pull-right
            try:
                reviews_el = card.find_element(
                    By.CSS_SELECTOR, ".ratings p.pull-right"
                )
                reviews_val = _parse_reviews(reviews_el.text)
            except NoSuchElementException:
                reviews_val = 0

            products.append(
                Product(
                    title=title_text,
                    description=desc_text,
                    price=price_val,
                    rating=rating_val,
                    num_of_reviews=reviews_val,
                )
            )
        except (NoSuchElementException, StaleElementReferenceException):
            # пропускаємо проблемні картки
            continue

    return products


def _save_csv(filename: str, products: Iterable[Product]) -> None:
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["title", "description", "price", "rating", "num_of_reviews"])
        for p in products:
            writer.writerow([p.title, p.description, f"{p.price:.2f}", p.rating,
                             p.num_of_reviews])


# ---------- Main orchestration ----------

def _scrape_page(
    driver: webdriver.Chrome,
    url: str,
    csv_name: str,
    has_more_button: bool,
) -> None:
    driver.get(url)
    _accept_cookies_if_present(driver)
    _wait_products_present(driver)

    if has_more_button:
        _click_more_until_exhausted(driver)

    products = _extract_products(driver)
    _save_csv(csv_name, products)


def get_all_products() -> None:
    """
    Скрейпить 6 сторінок:
      - home (3 товари, випадкові) -> home.csv
      - computers (3 випадкових) -> computers.csv
      - laptops (117) з пагінацією More -> laptops.csv
      - tablets (21) з пагінацією More -> tablets.csv
      - phones (3 випадкових) -> phones.csv
      - touch (9) з пагінацією More -> touch.csv
    """
    driver = _create_driver(headless=True)
    try:
        pages = [
            # (url, out_csv, has_more)
            (HOME_URL, "home.csv", False),
            (urljoin(HOME_URL, "computers"), "computers.csv", False),
            (urljoin(HOME_URL, "computers/laptops"), "laptops.csv", True),
            (urljoin(HOME_URL, "computers/tablets"), "tablets.csv", True),
            (urljoin(HOME_URL, "phones"), "phones.csv", False),
            (urljoin(HOME_URL, "phones/touch"), "touch.csv", True),
        ]
        for url, out_csv, need_more in pages:
            _scrape_page(driver, url, out_csv, need_more)
    finally:
        driver.quit()


if __name__ == "__main__":
    get_all_products()
