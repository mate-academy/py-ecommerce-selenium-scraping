from dataclasses import dataclass, asdict
from urllib.parse import urljoin
import csv
import re
from typing import Iterable

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions


BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


_PRICE_RE = re.compile(r"[-+]?\d*\.?\d+")
_REVIEWS_RE = re.compile(r"(\d+)")


def _parse_price(text: str) -> float:
    cleaned = text.replace(",", "")
    match_obj = _PRICE_RE.search(cleaned)
    return float(match_obj.group(0)) if match_obj else 0.0


def _parse_reviews(text: str) -> int:
    match_obj = _REVIEWS_RE.search(text)
    return int(match_obj.group(1)) if match_obj else 0


def _parse_products_from_html(html: str) -> list[Product]:
    soup = BeautifulSoup(html, "html.parser")
    blocks = soup.select("div.thumbnail")

    products: list[Product] = []

    for block in blocks:
        title_el = block.select_one("a.title")
        desc_el = block.select_one("p.description")
        price_el = block.select_one("h4.price")
        reviews_el = block.select_one("p.review-count")
        rating_el = block.select_one("[data-rating]")

        if not (title_el and desc_el and price_el):
            continue

        rating = int(rating_el["data-rating"]) if rating_el else 0

        products.append(
            Product(
                title=title_el.get_text(strip=True),
                description=desc_el.get_text(strip=True),
                price=_parse_price(price_el.get_text()),
                rating=rating,
                num_of_reviews=_parse_reviews(reviews_el.get_text()
                                              if reviews_el else "0"),
            )
        )

    return products


def _click_accept_cookies(driver: webdriver.Chrome) -> None:
    try:
        accept_btn = WebDriverWait(driver, 3).until(
            expected_conditions.element_to_be_clickable
            ((By.XPATH, "//button[contains(., 'Accept')]"))
        )
        accept_btn.click()
    except Exception:
        pass


def _load_all_products(driver: webdriver.Chrome) -> None:
    wait = WebDriverWait(driver, 10)

    while True:
        try:
            more_button = wait.until(
                expected_conditions.presence_of_element_located
                ((By.CSS_SELECTOR, "a.ecomerce-items-scroll-more"))
            )
        except Exception:
            break

        if not more_button.is_displayed():
            break

        current_count = len(driver.find_elements
                            (By.CSS_SELECTOR, "div.thumbnail"))
        more_button.click()

        try:
            wait.until(
                lambda d: len(
                    d.find_elements(
                        By.CSS_SELECTOR, "div.thumbnail")) > current_count
            )
        except Exception:
            break


def _scrape_page(driver: webdriver.Chrome, url: str, load_all: bool) \
        -> list[Product]:
    driver.get(url)

    WebDriverWait(driver, 10).until(
        expected_conditions.presence_of_element_located(
            (By.CSS_SELECTOR, "div.thumbnail"))
    )

    _click_accept_cookies(driver)

    if load_all:
        _load_all_products(driver)

    html = driver.page_source
    return _parse_products_from_html(html)


def _write_csv(products: Iterable[Product], filename: str) -> None:
    with open(filename, "w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(
            csv_file,
            fieldnames=["title",
                        "description",
                        "price",
                        "rating",
                        "num_of_reviews"],
        )
        writer.writeheader()
        for product in products:
            writer.writerow(asdict(product))


def get_driver() -> webdriver.Chrome:
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--window-size=1920,1080")
    return webdriver.Chrome(options=options)


def get_all_products() -> None:
    driver = get_driver()

    try:
        pages = [
            ("home.csv", HOME_URL, False),
            ("computers.csv", urljoin(HOME_URL, "computers"), False),
            ("laptops.csv", urljoin(HOME_URL, "computers/laptops"), True),
            ("tablets.csv", urljoin(HOME_URL, "computers/tablets"), True),
            ("phones.csv", urljoin(HOME_URL, "phones"), False),
            ("touch.csv", urljoin(HOME_URL, "phones/touch"), True),
        ]

        for filename, url, load_all in pages:
            products = _scrape_page(driver, url, load_all)
            _write_csv(products, filename)

    finally:
        driver.quit()


if __name__ == "__main__":
    get_all_products()
