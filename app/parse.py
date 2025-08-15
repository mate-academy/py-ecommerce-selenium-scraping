import csv
import logging
import sys
import random
import time
from dataclasses import dataclass, fields, astuple
from urllib.parse import urljoin

from bs4 import Tag, BeautifulSoup
from selenium import webdriver
from selenium.common import (
    NoSuchElementException,
    ElementClickInterceptedException,
    TimeoutException
)
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec


BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")

COMPUTERS_URL = urljoin(HOME_URL, "computers")
LAPTOPS_URL = urljoin(COMPUTERS_URL, "computers/laptops")
TABLETS_URL = urljoin(COMPUTERS_URL, "computers/tablets")

PHONES_URL = urljoin(HOME_URL, "phones")
TOUCH_URL = urljoin(PHONES_URL, "phones/touch")

_driver: WebDriver | None = None


def get_driver() -> WebDriver:
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

logging.basicConfig(
    level=logging.DEBUG,
    format="[%(levelname)8s]: %(message)s",
    handlers=[
        logging.FileHandler("parser.log"),
        logging.StreamHandler(sys.stdout)
    ]
)


def accept_cookies_if_present(driver: WebDriver, timeout: int = 5) -> None:
    try:
        button = WebDriverWait(driver, timeout).until(
            ec.element_to_be_clickable((
                By.CSS_SELECTOR, "button#accept-cookies, .cookie-accept"
            ))
        )
        if button.is_displayed() and button.is_enabled():
            logging.info("Clicking 'Accept Cookies' button")
            button.click()
            time.sleep(1)
    except TimeoutException:
        logging.info("No 'Accept Cookies' button found on this page")
    except Exception as e:
        logging.warning(
            f"Unexpected error while clicking 'Accept Cookies': {e}"
        )


def clean_text(text: str) -> str:
    if not text:
        return ""
    return text.replace("\xa0", " ").strip()


def parse_single_product(product: Tag) -> Product:
    star_icons = product.select("span.ws-icon.ws-icon-star")
    num_reviews_tag = product.select_one(".review-count")

    title_element = product.select_one("h4 a.title, a.title, h4 a")
    title = clean_text(
        title_element.get("title") or title_element.text
    ) if title_element else ""
    if title_element:
        logging.debug(f"Parsed product title: '{title}'")
    else:
        logging.warning("No title found for product")

    description_elem = product.select_one(".description")
    description = clean_text(description_elem.text) if description_elem else ""

    price_elem = product.select_one(".price")
    price = 0.0
    if price_elem:
        try:
            price_text = price_elem.text.replace(
                "$", "").replace(",", ""
                                 )
            price = float(price_text)
        except (ValueError, AttributeError) as e:
            logging.warning(
                f"Could not parse price: "
                f"{price_elem.text if price_elem else 'None'} - {e}"
            )

    return Product(
        title=title,
        description=description,
        price=price,
        rating=len(star_icons),
        num_of_reviews=int(
            num_reviews_tag.text.split()[0]) if num_reviews_tag else 0,
    )


def get_single_page_products(soup: BeautifulSoup) -> list[Product]:
    products = soup.select(".card-body, .thumbnail .caption")
    return [parse_single_product(product) for product in products]


def get_random_products(
        url: str,
        driver: WebDriver,
        count: int = 3
) -> list[Product]:
    logging.info(f"Start parsing random products from: {url}")
    driver.get(url)
    time.sleep(2)
    accept_cookies_if_present(driver)
    time.sleep(1)

    soup = BeautifulSoup(driver.page_source, "html.parser")
    products_html = soup.select(".card-body, .thumbnail .caption")

    sample_products = random.sample(
        products_html, k=min(count, len(products_html))
    )

    return [
        parse_single_product(product_soup) for product_soup in sample_products
    ]


def product_key(product_html: Tag) -> str:
    title_tag = product_html.select_one("h4 a.title, a.title, h4 a")
    desc_tag = product_html.select_one(".description")
    price_tag = product_html.select_one(".price")

    title = clean_text(
        title_tag.get("title") or title_tag.text
    ) if title_tag else ""
    desc = clean_text(desc_tag.text) if desc_tag else ""
    price = price_tag.text.strip() if price_tag else ""

    return f"{title}|{desc}|{price}"


def get_products_from_page(url: str, driver: WebDriver) -> list[Product]:
    logging.info(f"Start parsing page: {url}")
    driver.get(url)
    time.sleep(2)
    accept_cookies_if_present(driver)
    time.sleep(1)

    all_products = []
    seen_keys = set()
    page_count = 1
    consecutive_no_new_products = 0
    max_consecutive_attempts = 3

    while consecutive_no_new_products < max_consecutive_attempts:
        logging.info(f"Processing page/batch {page_count}")

        try:
            WebDriverWait(driver, 10).until(
                ec.presence_of_element_located((
                    By.CSS_SELECTOR, ".card-body, .thumbnail .caption"
                ))
            )
        except TimeoutException:
            logging.warning("Timeout waiting for products to load")
            break

        soup = BeautifulSoup(driver.page_source, "html.parser")
        products_html = soup.select(".card-body, .thumbnail .caption")

        logging.info(
            f"Found {len(products_html)} total products on current page"
        )

        new_products_count = 0
        for p_html in products_html:
            key = product_key(p_html)
            if key not in seen_keys:
                seen_keys.add(key)
                try:
                    product = parse_single_product(p_html)
                    all_products.append(product)
                    new_products_count += 1
                except Exception as e:
                    logging.warning(f"Error parsing product: {e}")
                    continue

        logging.info(f"Added {new_products_count} new products "
                     f"(total: {len(all_products)})")

        if new_products_count == 0:
            consecutive_no_new_products += 1
            logging.info(
                f"No new products found, attempt "
                f"{consecutive_no_new_products}/{max_consecutive_attempts}"
            )
        else:
            consecutive_no_new_products = 0

        try:
            more_button = WebDriverWait(driver, 5).until(
                ec.element_to_be_clickable((
                    By.CSS_SELECTOR, ".ecomerce-items-scroll-more"
                ))
            )

            if more_button.is_displayed() and more_button.is_enabled():
                logging.info("Clicking 'More' button")
                driver.execute_script("arguments[0].click();", more_button)
                time.sleep(3)
                page_count += 1
            else:
                logging.info("'More' button not clickable, ending pagination")
                break

        except (NoSuchElementException, TimeoutException):
            logging.info("No 'More' button found, reached end of products")
            break
        except ElementClickInterceptedException as e:
            logging.warning(f"Could not click 'More' button: {e}")
            try:
                driver.execute_script(
                    "arguments[0].scrollIntoView();", more_button
                )
                time.sleep(1)
                driver.execute_script("arguments[0].click();", more_button)
                time.sleep(3)
                page_count += 1
            except Exception as e2:
                logging.warning(
                    f"Second attempt to click 'More' button failed: {e2}"
                )
                break
        except Exception as e:
            logging.error(f"Unexpected error with 'More' button: {e}")
            break

    logging.info(
        f"Finished scraping. Total products collected: {len(all_products)}"
    )
    return all_products


def write_products_to_csv(products: list[Product], filename: str) -> None:
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(PRODUCT_FIELDS)
        writer.writerows([astuple(product) for product in products])


def get_all_products() -> None:
    options = webdriver.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    with webdriver.Chrome(options=options) as driver:
        set_driver(driver)

        full_pages = [
            (LAPTOPS_URL, "laptops.csv"),
            (TABLETS_URL, "tablets.csv"),
            (TOUCH_URL, "touch.csv"),
        ]

        for url, filename in full_pages:
            try:
                products = get_products_from_page(url, driver)
                write_products_to_csv(products, filename)
                logging.info(f"Saved {len(products)} products to {filename}")
            except Exception as e:
                logging.error(f"Error processing {url}: {e}")

        random_pages = [
            (HOME_URL, "home.csv"),
            (COMPUTERS_URL, "computers.csv"),
            (PHONES_URL, "phones.csv"),
        ]

        for url, filename in random_pages:
            try:
                products = get_random_products(url, driver, count=3)
                write_products_to_csv(products, filename)
                logging.info(
                    f"Saved {len(products)} random products to {filename}"
                )
            except Exception as e:
                logging.error(f"Error processing {url}: {e}")


if __name__ == "__main__":
    get_all_products()
