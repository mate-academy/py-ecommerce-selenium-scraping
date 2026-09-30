import csv
import logging
import sys
from dataclasses import dataclass, fields, astuple, field
from urllib.parse import urljoin

from bs4 import Tag, BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more")
COMPUTERS_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/computers")
LAPTOP_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/computers/laptops")
TABLETS_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/computers/tablets")
PHONES_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/phones")
TOUCH_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/phones/touch")

PAGES = {
    "home": HOME_URL,
    "computers": COMPUTERS_URL,
    "laptops": LAPTOP_URL,
    "tablets": TABLETS_URL,
    "phones": PHONES_URL,
    "touch": TOUCH_URL,
}

_driver: WebDriver | None = None


def get_driver() -> WebDriver | None:
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
    additional_info: dict = field(default_factory=dict, compare=False)


PRODUCT_FIELDS = [field.name for field in fields(Product)]

logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)8s]:  %(message)s",
    handlers=[
        logging.FileHandler("parser.log"),
        logging.StreamHandler(sys.stdout),
    ]
)


def accept_cookies(driver: WebDriver) -> None:
    try:
        WebDriverWait(driver, 2).until(
            ec.element_to_be_clickable((By.CLASS_NAME, "acceptCookies"))
        ).click()
    except TimeoutException:
        pass


def load_all_products(driver: WebDriver) -> None:
    while True:
        try:
            button = driver.find_element(
                By.CLASS_NAME, "ecomerce-items-scroll-more"
            )
        except NoSuchElementException:
            return
        if not button.is_displayed():
            return
        before = len(driver.find_elements(By.CLASS_NAME, "card-body"))
        driver.execute_script("arguments[0].click();", button)
        try:
            WebDriverWait(driver, 5).until(
                lambda d: len(d.find_elements(
                    By.CLASS_NAME, "card-body")
                ) > before
            )
        except TimeoutException:
            return


def parse_hdd_block_prices(product_soup: Tag) -> dict[str, float]:
    absolute_url = urljoin(BASE_URL, product_soup.select_one(".title")["href"])
    driver = get_driver()
    driver.get(absolute_url)
    try:
        swatches = driver.find_element(By.CLASS_NAME, "swatches")
    except NoSuchElementException:
        return {}

    prices = {}
    for button in swatches.find_elements(By.TAG_NAME, "button"):
        if not button.get_property("disabled"):
            old_price = driver.find_element(By.CLASS_NAME, "price").text
            driver.execute_script("arguments[0].click();", button)
            try:
                WebDriverWait(driver, 1).until(
                    lambda d: d.find_element(
                        By.CLASS_NAME, "price"
                    ).text != old_price
                )
            except TimeoutException:
                pass
            prices[button.get_attribute("value")] = float(
                driver.find_element(
                    By.CLASS_NAME, "price")
                .text.replace("$", "")
            )
    return prices


def parse_single_product(product: Tag) -> Product:
    hdd_prices = parse_hdd_block_prices(product)
    return Product(
        title=product.select_one(".title")["title"],
        description=product.select_one(
            ".description").text.replace("\xa0", " "
                                         ),
        price=float(product.select_one(".price").text.replace("$", "")),
        rating=len(product.select("span.ws-icon-star")),
        num_of_reviews=int(
            product.select_one(".review-count").text.split()[0]
        ),
        additional_info={"hdd_prices": hdd_prices},
    )


def get_page_products(url: str) -> list[Product]:
    driver = get_driver()
    driver.get(url)
    accept_cookies(driver)
    load_all_products(driver)
    soup = BeautifulSoup(driver.page_source, "html.parser")
    return [parse_single_product(card) for card in soup.select(".card-body")]


def write_products_to_csv(products: list[Product], filename: str) -> None:
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(PRODUCT_FIELDS)
        writer.writerows([astuple(product) for product in products])


def get_all_products() -> None:
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--window-size=1920,1080")
    with webdriver.Chrome(options=options) as driver:
        set_driver(driver)
        for name, url in PAGES.items():
            logging.info(f"Start parsing {name}")
            write_products_to_csv(get_page_products(url), f"{name}.csv")


if __name__ == "__main__":
    get_all_products()
