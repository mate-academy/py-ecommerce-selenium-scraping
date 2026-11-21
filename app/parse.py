import csv
import logging
from collections.abc import Generator
from contextlib import contextmanager
from dataclasses import astuple, dataclass, fields
from urllib.parse import urljoin

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")

# output file name -> page path relative to HOME_URL
PAGES = {
    "home": "",
    "computers": "computers",
    "laptops": "computers/laptops",
    "tablets": "computers/tablets",
    "phones": "phones",
    "touch": "phones/touch",
}

PRODUCT_SELECTOR = "div.product-wrapper"
MORE_BUTTON_SELECTOR = "a.ecomerce-items-scroll-more"  # the typo is on the site itself
COOKIES_BUTTON_SELECTOR = "button.acceptCookies"
STAR_SELECTOR = "span.ws-icon-star"
WAIT_SECONDS = 10


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


@contextmanager
def create_driver() -> Generator[WebDriver, None, None]:
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    logger.info("Starting Chrome driver")
    driver = webdriver.Chrome(options=options)
    try:
        yield driver
    finally:
        driver.quit()
        logger.info("Chrome driver closed")


def accept_cookies(driver: WebDriver) -> None:
    try:
        WebDriverWait(driver, 3).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, COOKIES_BUTTON_SELECTOR))
        ).click()
        logger.info("Cookies banner accepted")
    except TimeoutException:
        logger.info("No cookies banner")


def count_products(driver: WebDriver) -> int:
    return len(driver.find_elements(By.CSS_SELECTOR, PRODUCT_SELECTOR))


def load_all_products(driver: WebDriver) -> None:
    """Click the 'more' button until it disappears (or does nothing)."""
    clicks = 0
    while True:
        buttons = driver.find_elements(By.CSS_SELECTOR, MORE_BUTTON_SELECTOR)
        if not buttons or not buttons[0].is_displayed():
            logger.info("'More' button gone after %d click(s)", clicks)
            return

        before = count_products(driver)
        driver.execute_script("arguments[0].click();", buttons[0])
        clicks += 1
        try:
            WebDriverWait(driver, WAIT_SECONDS).until(
                lambda d: count_products(d) > before
            )
            logger.info("Click %d: %d -> %d products", clicks, before, count_products(driver))
        except TimeoutException:
            logger.warning("Click %d: no new products after %ds, stopping", clicks, WAIT_SECONDS)
            return


def parse_product(element: WebElement) -> Product:
    try:
        return Product(
            title=element.find_element(By.CSS_SELECTOR, "a.title").get_attribute("title"),
            description=element.find_element(By.CSS_SELECTOR, "p.description").text,
            price=float(
                element.find_element(By.CSS_SELECTOR, "h4.price").text.replace("$", "")
            ),
            rating=len(element.find_elements(By.CSS_SELECTOR, STAR_SELECTOR)),
            num_of_reviews=int(
                element.find_element(By.CSS_SELECTOR, "p.review-count").text.split()[0]
            ),
        )
    except Exception:
        logger.error("Failed to parse product, its HTML:\n%s", element.get_attribute("outerHTML"))
        raise


def scrape_page(driver: WebDriver, name: str, url: str) -> list[Product]:
    logger.info("[%s] Opening %s", name, url)
    driver.get(url)
    accept_cookies(driver)
    load_all_products(driver)

    elements = driver.find_elements(By.CSS_SELECTOR, PRODUCT_SELECTOR)
    logger.info("[%s] Parsing %d products", name, len(elements))
    return [parse_product(element) for element in elements]


def write_products_to_csv(products: list[Product], output_csv_path: str) -> None:
    with open(output_csv_path, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow([field.name for field in fields(Product)])
        writer.writerows(astuple(product) for product in products)
    logger.info("Saved %d products to %s", len(products), output_csv_path)


def get_all_products() -> None:
    with create_driver() as driver:
        for name, path in PAGES.items():
            products = scrape_page(driver, name, urljoin(HOME_URL, path))
            write_products_to_csv(products, f"{name}.csv")
    logger.info("Done: all %d pages scraped", len(PAGES))


if __name__ == "__main__":
    get_all_products()