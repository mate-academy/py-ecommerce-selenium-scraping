import csv
import logging
import time
from dataclasses import dataclass, fields, astuple
from urllib.parse import urljoin

from selenium.common import TimeoutException
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
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
    stars = card.find_all("span", class_="ws-icon-star")
    return len(stars) if stars else 0


def parse_single_product(product: Tag) -> Product:
    title_el = product.select_one(".title")
    title = title_el["title"] if title_el and title_el.has_attr("title") else (
        title_el.text.strip() if title_el else "Unknown")

    desc_el = product.select_one(".description")
    description = desc_el.text.replace("\xa0", " ").strip() if desc_el else ""

    price_el = product.select_one(".price")
    price = float(price_el.text.replace("$", "").strip()) if price_el else 0.0

    reviews_el = product.select_one(".review-count")
    num_of_reviews = 0
    if reviews_el:
        reviews_text = reviews_el.text.split()
        if reviews_text:
            num_of_reviews = int(reviews_text[0])

    return Product(
        title=title,
        description=description,
        price=price,
        rating=get_rating(product),
        num_of_reviews=num_of_reviews,
    )


def parse_single_page(page_soup: Tag) -> list[Product]:
    products = page_soup.select(".card-body")
    return [parse_single_product(product) for product in products]


def write_products_to_csv(file_name: str, products: list[Product]) -> None:
    with open(f"{file_name}.csv", "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(PRODUCT_FIELDS)
        writer.writerows([astuple(product) for product in products])


_REMOVE_TERMLY_JS = """
document.querySelectorAll('[class*="termly"]').forEach(el => el.remove());
document.body.style.overflow = 'auto';
document.documentElement.style.overflow = 'auto';
"""


def dismiss_cookie_banner(driver: WebDriver) -> None:
    time.sleep(1.0)  # Даємо банеру мить для завантаження
    driver.execute_script(_REMOVE_TERMLY_JS)


def scrape_page(url: str, driver: WebDriver) -> list[Product]:
    driver.get(url)
    dismiss_cookie_banner(driver)

    button_locator = (By.CLASS_NAME, "ecomerce-items-scroll-more")
    card_locator = (By.CLASS_NAME, "card-body")

    logging.info(f"Starting parsing data from {url}")

    while True:
        try:
            button = WebDriverWait(driver, 4).until(
                ec.presence_of_element_located(button_locator)
            )

            if not button.is_displayed():
                break

            prev_count = len(driver.find_elements(*card_locator))

            driver.execute_script(_REMOVE_TERMLY_JS)

            driver.execute_script("arguments[0].click();", button)

            WebDriverWait(driver, 8).until(
                lambda d: len(d.find_elements(*card_locator)) > prev_count
            )
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
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument(
        "--user-agent=Mozilla/5.0 "
        "(Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )

    driver = webdriver.Chrome(options=options)

    try:
        for page_name, page_url in tqdm(PAGES.items(), desc="Scraping pages"):
            products = scrape_page(page_url, driver)
            write_products_to_csv(page_name, products)
    finally:
        driver.quit()


if __name__ == "__main__":
    get_all_products()
