import csv
import time
import unicodedata
from dataclasses import astuple, dataclass, fields
from urllib.parse import urljoin

from bs4 import BeautifulSoup, Tag
from selenium import webdriver
from selenium.common import WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")
COMPUTERS_URL = urljoin(HOME_URL, "computers/")
LAPTOPS_URL = urljoin(COMPUTERS_URL, "laptops")
TABLETS_URL = urljoin(COMPUTERS_URL, "tablets")
PHONES_URL = urljoin(HOME_URL, "phones/")
TOUCH_URL = urljoin(PHONES_URL, "touch")

SCRAPE_TO_CSV = [
    (HOME_URL, "home.csv"),
    (COMPUTERS_URL, "computers.csv"),
    (LAPTOPS_URL, "laptops.csv"),
    (TABLETS_URL, "tablets.csv"),
    (PHONES_URL, "phones.csv"),
    (TOUCH_URL, "touch.csv"),
]

_driver: WebDriver | None = None


def get_driver() -> WebDriver:
    if _driver is None:
        raise RuntimeError("Driver not set; call set_driver() first")
    return _driver


def set_driver(new_driver: WebDriver) -> None:
    global _driver
    _driver = new_driver


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


PRODUCT_FIELDS = [field.name for field in fields(Product)]


def normalize_text(text: str) -> str:
    """Normalize text: deletes spaces and invisible chars"""
    if not text:
        return text

    text = text.replace("\xa0", " ")
    text = text.replace("\u200b", "")
    text = text.replace("\u2009", " ")
    text = text.replace("\u202f", " ")
    text = " ".join(text.split())
    text = unicodedata.normalize("NFKC", text)
    return text.strip()


def check_and_accept_cookies(driver: WebDriver) -> None:
    cookies = driver.find_elements(By.ID, "cookieBanner")
    if cookies:
        try:
            accept_cookies = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.CLASS_NAME, "acceptCookies"))
            )
            accept_cookies.click()
        except WebDriverException:
            pass


def check_and_click_more_buttons(driver: WebDriver) -> None:
    try:
        while True:
            time.sleep(1)
            more_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable(
                    (By.CLASS_NAME, "ecomerce-items-scroll-more")
                )
            )
            more_button.click()
    except WebDriverException:
        pass


def parse_product(product: Tag) -> Product:
    price = product.select_one(".price").text.replace("$", "")
    if not price:
        price = product.select_one(
            "span[itemprop='price']"
        ).text.replace("$", "")

    rating = len(product.select(".ws-icon-star"))
    if not rating:
        rating = int(product.select_one("p[data-rating]")["data-rating"])

    pr = Product(
        title=normalize_text(product.select_one(".title")["title"]),
        description=normalize_text(product.select_one(".description").text),
        price=float(price),
        rating=rating,
        num_of_reviews=int(product.select_one(
            "span[itemprop='reviewCount']"
        ).text),
    )
    print(pr)
    return pr


def get_products_from_page(url: str, driver: WebDriver) -> list[Product]:
    driver.get(url)
    check_and_accept_cookies(driver)
    check_and_click_more_buttons(driver)
    soup = BeautifulSoup(driver.page_source, "html.parser")
    products = soup.select("div.product-wrapper")
    return [parse_product(product) for product in products]


def get_all_products() -> None:
    driver = webdriver.Edge()
    set_driver(driver)

    for url, filename in SCRAPE_TO_CSV:
        products = get_products_from_page(url, driver)
        write_to_csv(filename, products)

    driver.quit()


def write_to_csv(csv_file: str, products: list[Product]) -> None:
    with open(csv_file, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(PRODUCT_FIELDS)
        writer.writerows(astuple(product) for product in products)


if __name__ == "__main__":
    get_all_products()
