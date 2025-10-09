import csv
import random
import logging
import sys
import json
from dataclasses import dataclass, fields
from urllib.parse import urljoin
from bs4 import BeautifulSoup, Tag
from selenium import webdriver
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
)


BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")

_driver: WebDriver | None = None


def get_driver() -> WebDriver:
    return _driver


def set_driver(driver: WebDriver) -> None:
    global _driver
    _driver = driver


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int
    additional_info: dict


PRODUCT_FIELDS = [f.name for f in fields(Product)]

logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)8s]:  %(message)s",
    handlers=[
        logging.FileHandler("products.log"),
        logging.StreamHandler(sys.stdout)
    ]
)


# === HELPERS ===
def accept_cookies_if_present(driver: WebDriver) -> None:
    """Click 'Accept cookies' if the banner appears."""
    try:
        WebDriverWait(driver, 3).until(
            EC.presence_of_element_located((By.ID, "accept-cookies"))
        )
        driver.find_element(By.ID, "accept-cookies").click()
    except Exception:
        pass


def parse_hdd_block_prices(product_soup: Tag) -> dict[str, float]:
    """Open product detail page and get HDD/variant prices if exist."""
    absolute_url = urljoin(HOME_URL, product_soup.select_one(".title")["href"])
    driver = get_driver()

    if driver is None:
        raise RuntimeError("WebDriver is not initialized. Call set_driver() first.")

    driver.get(absolute_url)
    wait = WebDriverWait(driver, 10)

    try:
        swatches = wait.until(
            EC.presence_of_element_located((By.CLASS_NAME, "swatches"))
        )
    except TimeoutException:
        return {}

    buttons = swatches.find_elements(By.TAG_NAME, "button")
    prices = {}

    for button in buttons:
        if not button.get_property("disabled"):
            value = button.get_property("value")
            button.click()
            try:
                wait.until(EC.text_to_be_present_in_element((By.CLASS_NAME, "price"), "$"))
                price_el = driver.find_element(By.CLASS_NAME, "price")
                prices[value] = float(price_el.text.replace("$", ""))
            except TimeoutException:
                logging.warning(f"Timeout updating price for {absolute_url}")
            except NoSuchElementException:
                logging.warning(f"No price element on {absolute_url}")

    return prices


def parse_single_page_product(product: Tag) -> Product:
    """Parse product card from a page soup."""
    hdd_prices = parse_hdd_block_prices(product) if product.select_one(".swatches") else {}

    return Product(
        title=product.select_one(".title")["title"],
        description=product.select_one(".description").text,
        price=float(product.select_one(".price").text.replace("$", "")),
        rating=int(product.select_one("p[data-rating]")["data-rating"]),
        num_of_reviews=int(product.select_one(".review-count").text.split()[0]),
        additional_info={"hdd_prices": hdd_prices},
    )


def get_random_products_from_page(url: str, count: int = 3) -> list[Product]:
    """Open page and parse 3 random products."""
    driver = get_driver()
    if driver is None:
        raise RuntimeError("WebDriver is not initialized.")

    driver.get(url)
    accept_cookies_if_present(driver)
    soup = BeautifulSoup(driver.page_source, "html.parser")

    products = soup.select(".card-body")
    if not products:
        logging.warning(f"No products found at {url}")
        return []

    n = min(count, len(products))
    selected = random.sample(products, n)
    return [parse_single_page_product(p) for p in selected]


def get_all_products_with_more_button(url: str) -> list[Product]:
    """Open page, repeatedly click 'More' button until all products are loaded."""
    driver = get_driver()
    if driver is None:
        raise RuntimeError("WebDriver is not initialized.")

    driver.get(url)
    accept_cookies_if_present(driver)

    while True:
        try:
            products_before = len(driver.find_elements(By.CLASS_NAME, "card-body"))
            more_button = driver.find_element(By.CLASS_NAME, "btn-primary")
            driver.execute_script("arguments[0].click();", more_button)

            WebDriverWait(driver, 5).until(
                lambda d: len(d.find_elements(By.CLASS_NAME, "card-body")) > products_before
            )
        except (NoSuchElementException, TimeoutException):
            break

    soup = BeautifulSoup(driver.page_source, "html.parser")
    products = soup.select(".card-body")
    return [parse_single_page_product(p) for p in products]


def get_home_products() -> list[Product]:
    return get_random_products_from_page(HOME_URL, 3)


def get_computers_products() -> list[Product]:
    return get_random_products_from_page(urljoin(HOME_URL, "computers"), 3)


def get_phones_products() -> list[Product]:
    return get_random_products_from_page(urljoin(HOME_URL, "phones"), 3)


def get_laptop_page_products() -> list[Product]:
    return get_all_products_with_more_button(urljoin(HOME_URL, "computers/laptops"))


def get_tablets_products() -> list[Product]:
    return get_all_products_with_more_button(urljoin(HOME_URL, "computers/tablets"))


def get_touch_products() -> list[Product]:
    return get_all_products_with_more_button(urljoin(HOME_URL, "phones/touch"))


def write_products_to_csv(products: list[Product], filename: str) -> None:
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(PRODUCT_FIELDS)
        for p in products:
            row = [
                p.title,
                p.description,
                p.price,
                p.rating,
                p.num_of_reviews,
                json.dumps(p.additional_info, ensure_ascii=False),
            ]
            writer.writerow(row)


def get_all_products() -> None:
    pages = {
        "home": get_home_products,
        "computers": get_computers_products,
        "laptops": get_laptop_page_products,
        "tablets": get_tablets_products,
        "phones": get_phones_products,
        "touch": get_touch_products,
    }

    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    with webdriver.Chrome(options=options) as driver:
        set_driver(driver)
        for name, func in pages.items():
            logging.info(f"Scraping {name} page...")
            products = func()
            write_products_to_csv(products, f"{name}.csv")
            logging.info(f"✅ {len(products)} products saved to {name}.csv")


def main() -> None:
    get_all_products()


if __name__ == "__main__":
    main()
