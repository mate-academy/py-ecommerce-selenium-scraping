import re
import csv
import sys
import time
import logging
from pathlib import Path
from urllib.parse import urljoin
from dataclasses import dataclass, fields, astuple

import requests
from tqdm import tqdm
from bs4 import BeautifulSoup, Tag

from selenium.common.exceptions import (
    WebDriverException,
    ElementClickInterceptedException,
    ElementNotInteractableException,
)
from selenium import webdriver
from selenium.common import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as ec

BASE_URL = "https://webscraper.io/"

HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")

COMPUTERS_URL = urljoin(HOME_URL, "computers/")
LAPTOPS_URL = urljoin(COMPUTERS_URL, "laptops/")
TABLETS_URL = urljoin(COMPUTERS_URL, "tablets/")

PHONES_URL = urljoin(HOME_URL, "phones/")
TOUCH_URL = urljoin(PHONES_URL, "touch/")

logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)8s]:  %(message)s",
    handlers=[
        logging.FileHandler("parse.log"),
        logging.StreamHandler(sys.stdout)
    ]
)


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


PRODUCT_FIELDS = [field.name for field in fields(Product)]

PAGES = {
    "home": {
        "url": HOME_URL,
    },
    "computers": {
        "url": COMPUTERS_URL,
    },
    "phones": {
        "url": PHONES_URL,
    },
    "laptops": {
        "url": LAPTOPS_URL,
        "category": "Computers",
        "subcategory": "Laptops",
    },
    "tablets": {
        "url": TABLETS_URL,
        "category": "Computers",
        "subcategory": "Tablets",
    },
    "touch": {
        "url": TOUCH_URL,
        "category": "Phones",
        "subcategory": "Touch",
    },
}


def clean_text(text: str) -> str:
    text = text.replace("\xa0", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def parse_single_product(product_soup: Tag) -> Product:
    return Product(
        title=product_soup.select_one("a")["title"],
        description=clean_text(
            product_soup.select_one(".description").get_text(strip=True)
        ),
        price=float(
            product_soup.select_one(
                "[class*='price']"
            ).get_text(strip=True).replace("$", "")
        ),
        rating=len(product_soup.select(".ws-icon-star")),
        num_of_reviews=int(
            product_soup.select_one(
                "span[itemprop='reviewCount']"
            ).get_text(strip=True)
        ),
    )


def create_driver(headless: bool = True) -> webdriver.Chrome:
    options = Options()

    if headless:
        options.add_argument("--headless=new")

    try:
        return webdriver.Chrome(options=options)
    except WebDriverException:
        options = Options()
        options.add_argument("--headless")
        return webdriver.Chrome(options=options)


def handle_cookies(driver: WebDriver) -> None:
    try:
        btn = WebDriverWait(driver, 10).until(
            ec.element_to_be_clickable(
                (By.CSS_SELECTOR, "[data-tid*='cookie']")
            )
        )
        safe_click(driver, btn)
    except TimeoutException:
        pass


def safe_click(driver: WebDriver, element: WebElement) -> None:
    try:
        element.click()
    except (ElementClickInterceptedException, ElementNotInteractableException):
        driver.execute_script("arguments[0].click();", element)


def navigate_to_category(
        driver: WebDriver,
        category: str,
        subcategory: str
) -> None:
    handle_cookies(driver)

    category_link = WebDriverWait(driver, 10).until(
        ec.element_to_be_clickable((By.LINK_TEXT, category))
    )
    safe_click(driver, category_link)

    handle_cookies(driver)

    subcategory_link = WebDriverWait(driver, 10).until(
        ec.element_to_be_clickable((By.LINK_TEXT, subcategory))
    )
    safe_click(driver, subcategory_link)


def load_all_products(driver: WebDriver) -> None:
    while True:
        try:
            more_button = WebDriverWait(driver, 10).until(
                ec.element_to_be_clickable(
                    (By.CLASS_NAME, "ecomerce-items-scroll-more")
                )
            )
            safe_click(driver, more_button)
        except TimeoutException:
            break


def extract_products_from_soup(soup: BeautifulSoup) -> list[Product]:
    products = soup.select(".card-body")
    return [parse_single_product(product) for product in products]


def get_products_from_page(driver: WebDriver) -> list[Product]:
    html = driver.page_source
    soup = BeautifulSoup(html, "html.parser")
    return extract_products_from_soup(soup)


def parse_dynamic_page(
        category: str,
        subcategory: str
) -> list[Product]:
    if not category or not subcategory:
        raise ValueError(
            "Category and subcategory must be provided"
        )

    driver = create_driver()

    try:
        driver.get(HOME_URL)

        handle_cookies(driver)

        navigate_to_category(driver, category, subcategory)
        load_all_products(driver)

        return get_products_from_page(driver)

    finally:
        driver.quit()


def parse_static_page(url: str) -> list[Product]:
    retries = 3

    for attempt in range(retries):
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")
            return extract_products_from_soup(soup)

        except requests.RequestException:
            if attempt < retries - 1:
                time.sleep(1)
            else:
                page = next(
                    (p for p in PAGES.values() if p["url"] == url),
                    None
                )

                if page and "category" in page and "subcategory" in page:
                    return parse_dynamic_page(
                        page["category"],
                        page["subcategory"],
                    )

                raise RuntimeError(
                    f"Failed to fetch static page '{url}' after retries"
                )

    raise RuntimeError("Unreachable code in parse_static_page")


def has_more_button(url: str) -> bool:
    try:
        response = requests.get(url, timeout=10)
        text = response.text

        if "ecomerce-items-scroll-more" in text:
            return True

    except requests.RequestException as e:
        logging.warning(f"Request failed for {url}: {e}")

    driver = create_driver()
    try:
        driver.get(url)

        handle_cookies(driver)

        WebDriverWait(driver, 10).until(
            ec.presence_of_element_located(
                (By.CLASS_NAME, "ecomerce-items-scroll-more")
            )
        )
        return True

    except TimeoutException:
        return False

    finally:
        driver.quit()


def parse_page(page_name: str) -> list[Product]:
    page = PAGES[page_name]

    url = page["url"]

    if has_more_button(url):
        logging.info(f"Parsing {page_name} page using Selenium")

        if "category" not in page or "subcategory" not in page:
            raise ValueError(f"{page_name} missing category/subcategory")

        return parse_dynamic_page(
            category=page["category"],
            subcategory=page["subcategory"],
        )
    else:
        logging.info(f"Parsing {page_name} page using requests")

        return parse_static_page(url)


def write_products_to_csv(path: str, products: list[Product]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as _file:
        writer = csv.writer(_file)
        writer.writerow(PRODUCT_FIELDS)
        writer.writerows([astuple(product) for product in products])


def get_all_products(output_dir: str = ".") -> None:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    for page_name in tqdm(PAGES, desc="Parsing products"):
        products = parse_page(page_name)

        file_path = output_path / f"{page_name}.csv"
        write_products_to_csv(str(file_path), products)


if __name__ == "__main__":
    get_all_products("results")
