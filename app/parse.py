import csv
import re
from dataclasses import dataclass, fields, astuple
from urllib.parse import urljoin

import requests
from tqdm import tqdm
from bs4 import BeautifulSoup, Tag

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


def create_driver() -> webdriver.Chrome:
    options = Options()
    options.add_argument("--headless=new")
    return webdriver.Chrome(options=options)


def safe_click(driver: WebDriver, element: WebElement) -> None:
    try:
        element.click()
    except Exception:
        driver.execute_script("arguments[0].click();", element)


def navigate_to_category(
    driver: WebDriver,
    category: str,
    subcategory: str
) -> None:
    category_link = WebDriverWait(driver, 5).until(
        ec.element_to_be_clickable((By.LINK_TEXT, category))
    )
    safe_click(driver, category_link)

    subcategory_link = WebDriverWait(driver, 5).until(
        ec.element_to_be_clickable((By.LINK_TEXT, subcategory))
    )
    safe_click(driver, subcategory_link)


def load_all_products(driver: WebDriver) -> None:
    while True:
        try:
            more_button = WebDriverWait(driver, 5).until(
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
    driver = create_driver()
    driver.get(HOME_URL)

    navigate_to_category(driver, category, subcategory)
    load_all_products(driver)

    products = get_products_from_page(driver)

    driver.quit()
    return products


def parse_static_page(url: str) -> list[Product]:
    text = requests.get(url).text
    soup = BeautifulSoup(text, "html.parser")
    return extract_products_from_soup(soup)


def has_more_button(url: str) -> bool:
    text = requests.get(url).text
    return "ecomerce-items-scroll-more" in text


def parse_page(page_name: str) -> list[Product]:
    page = PAGES[page_name]

    url = page["url"]

    if has_more_button(url):
        print(f"> {page_name}: Selenium")

        return parse_dynamic_page(
            category=page.get("category"),
            subcategory=page.get("subcategory"),
        )
    else:
        print(f"> {page_name}: requests")

        return parse_static_page(url)


def write_products_to_cav(path: str, products: list[Product]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as _file:
        writer = csv.writer(_file)
        writer.writerow(PRODUCT_FIELDS)
        writer.writerows([astuple(product) for product in products])


def get_all_products() -> None:
    for page_name in tqdm(PAGES, desc="Parsing products"):
        products = parse_page(page_name)
        write_products_to_cav(f"{page_name}.csv", products)


if __name__ == "__main__":
    get_all_products()
