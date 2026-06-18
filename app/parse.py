import csv
import logging
import time
from dataclasses import dataclass, fields, astuple
from urllib.parse import urljoin

from selenium.common import TimeoutException, ElementClickInterceptedException
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from tqdm import tqdm
from bs4 import BeautifulSoup, Tag
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")
PAGES = {
    "home": HOME_URL,
    "computers": urljoin(HOME_URL, "computers"),
    "laptops": urljoin(HOME_URL, "computers/laptops"),
    "tablets": urljoin(HOME_URL, "computers/tablets"),
    "phones": urljoin(HOME_URL, "phones"),
    "touch": urljoin(HOME_URL, "phones/touch"),
}

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%H:%M:%S"
)


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


PRODUCT_FIELDS = [field.name for field in fields(Product)]


def get_rating(card: Tag) -> int:
    rating_tag = card.find("p", attrs={"data-rating": True})
    if rating_tag:
        return int(rating_tag["data-rating"])
    return len(card.find_all("span", class_="ws-icon-star"))


def parse_single_product(product: Tag) -> Product:
    return Product(
        title=product.select_one(".title")["title"],
        description=product.select_one(
            ".description"
        ).text.replace("\xa0", " "),
        price=float(product.select_one(".price").text.replace("$", "")),
        rating=get_rating(product),
        num_of_reviews=int(
            product.select_one(".review-count").text.split()[0]
        ),
    )


def parse_single_page(page_soup: Tag) -> list[Product]:
    products = page_soup.select(".card-body")
    return [parse_single_product(product) for product in products]


def write_products_to_csv(file_name: str, products: list[Product]) -> None:
    with open(f"{file_name}.csv", "w") as f:
        writer = csv.writer(f)
        writer.writerow(PRODUCT_FIELDS)
        writer.writerows([astuple(product) for product in products])


_REMOVE_TERMLY_JS = (
    "document.querySelectorAll("
    "'[class*=\"termly\"]'"
    ").forEach(el => el.remove());"
)


def dismiss_cookie_banner(driver: WebDriver) -> None:
    time.sleep(1.5)
    driver.execute_script(_REMOVE_TERMLY_JS)


def scrape_page(url: str, driver: WebDriver) -> list[Product]:
    driver.get(url)
    dismiss_cookie_banner(driver)

    button_locator = (By.CLASS_NAME, "ecomerce-items-scroll-more")
    card_locator = (By.CLASS_NAME, "card-body")

    logging.info(f"\nStarting parsing data from {url}")

    while True:
        try:
            button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable(button_locator)
            )
            prev_count = len(driver.find_elements(*card_locator))
            driver.execute_script(_REMOVE_TERMLY_JS)
            button.click()
            WebDriverWait(driver, 10).until(
                lambda d: len(d.find_elements(*card_locator)) > prev_count
            )
        except ElementClickInterceptedException:
            driver.execute_script(_REMOVE_TERMLY_JS)
        except TimeoutException:
            logging.info(f"Finished loading {url}. No more items to load.")
            break
        except Exception as e:
            logging.error(
                f"Unexpected error occurred during pagination: {e}",
                exc_info=True
            )
            break

    soup = BeautifulSoup(driver.page_source, "html.parser")
    return parse_single_page(soup)


def get_all_products() -> None:
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--window-size=1920,1080")

    driver = webdriver.Chrome(options=options)

    try:
        for page_name, page_url in tqdm(PAGES.items(), desc="Scraping pages"):
            products = scrape_page(page_url, driver)
            write_products_to_csv(page_name, products)
    finally:
        driver.quit()


if __name__ == "__main__":
    get_all_products()
