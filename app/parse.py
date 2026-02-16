import logging
import csv
import sys
from dataclasses import dataclass, asdict, fields
from urllib.parse import urljoin

from bs4 import BeautifulSoup, Tag
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.common.exceptions import (
    TimeoutException,
    ElementClickInterceptedException,
    StaleElementReferenceException,
)

BASE_URL = "https://webscraper.io/"
URLS = [
    urljoin(BASE_URL, "test-sites/e-commerce/more/"),
    urljoin(BASE_URL, "test-sites/e-commerce/more/computers"),
    urljoin(BASE_URL, "test-sites/e-commerce/more/computers/laptops"),
    urljoin(BASE_URL, "test-sites/e-commerce/more/computers/tablets"),
    urljoin(BASE_URL, "test-sites/e-commerce/more/phones"),
    urljoin(BASE_URL, "test-sites/e-commerce/more/phones/touch"),
]

_driver: WebDriver | None = None


def set_driver(driver: WebDriver) -> None:
    global _driver
    _driver = driver


def get_driver() -> WebDriver:
    return _driver


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


PRODUCT_FIELDS = [f.name for f in fields(Product)]

logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)


def accept_cookies_if_present(driver: WebDriver) -> None:
    try:
        button = WebDriverWait(driver, 3).until(
            ec.element_to_be_clickable(
                (
                    By.CSS_SELECTOR,
                    "button.accept,"
                    "button#accept,"
                    ".cookie-accept"
                )
            )
        )
        button.click()
        logging.info("Cookie banner accepted")
    except TimeoutException:
        pass


def expand_dynamic_content(
        driver: WebDriver,
        button_selector: str,
        items_selector: str = ".thumbnail",
        max_clicks: int = 20,
) -> None:
    clicks = 0

    while clicks < max_clicks:
        try:
            items_before = len(
                driver.find_elements(By.CSS_SELECTOR, items_selector)
            )

            button = WebDriverWait(driver, 5).until(
                ec.element_to_be_clickable((By.CSS_SELECTOR, button_selector))
            )

            driver.execute_script("arguments[0].click();", button)

            WebDriverWait(driver, 5).until(
                lambda d: len(
                    d.find_elements(By.CSS_SELECTOR, items_selector)
                ) > items_before
            )

            clicks += 1

        except TimeoutException:
            break
        except (
                ElementClickInterceptedException,
                StaleElementReferenceException
        ):
            logging.warning(
                "Retrying load-more click after interception/stale element"
            )
            continue


def safe_text(tag: Tag | None) -> str:
    return " ".join(tag.text.split()) if tag else ""


def safe_float(text: str) -> float:
    try:
        return float(text.replace("$", "").replace(",", "").strip())
    except ValueError:
        return 0.0


def safe_int(text: str) -> int:
    try:
        return int(text.strip())
    except ValueError:
        return 0


def parse_single_product(product_tag: Tag) -> Product:
    title_elem = product_tag.select_one(".title")
    if title_elem and title_elem.has_attr("title"):
        title = title_elem["title"]
    else:
        title = "No title"

    description = safe_text(product_tag.select_one(".description"))

    price_elem = product_tag.select_one(".price")
    price = safe_float(price_elem.text) if price_elem else 0.0

    rating_elem = product_tag.select_one("p[data-rating]")
    if rating_elem and rating_elem.has_attr("data-rating"):
        rating = safe_int(rating_elem["data-rating"])
    else:
        rating = len(product_tag.select(".ws-icon-star"))

    reviews_elem = product_tag.select_one(".review-count")
    num_of_reviews = (
        safe_int(reviews_elem.text.split()[0]) if reviews_elem else 0
    )

    return Product(
        title=title,
        description=description,
        price=price,
        rating=rating,
        num_of_reviews=num_of_reviews,
    )


def write_products_to_csv(products: list[Product], filename: str) -> None:
    if not products:
        logging.warning(f"{filename}: нет данных")
        return

    with open(filename, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=PRODUCT_FIELDS)
        writer.writeheader()
        for product in products:
            writer.writerow(asdict(product))


def get_all_products() -> None:
    options = webdriver.ChromeOptions()
    # options.add_argument("--headless")

    with (webdriver.Chrome(options=options) as driver):
        set_driver(driver)

        for url in URLS:
            logging.info(f"Processing category: {url}")
            driver.get(url)

            accept_cookies_if_present(driver)

            expand_dynamic_content(
                driver,
                button_selector="a.ecomerce-items-scroll-more",
            )

            soup = BeautifulSoup(driver.page_source, "html.parser")
            product_tags = soup.select(".thumbnail")

            products = [parse_single_product(tag) for tag in product_tags]

            if url.rstrip("/").endswith("/more"):
                name = "home"
            else:
                name = url.rstrip("/").split("/")[-1]

            write_products_to_csv(products, f"{name}.csv")


if __name__ == "__main__":
    get_all_products()
