import csv
import time
import logging
import sys
from dataclasses import dataclass, fields
from typing import List, Dict, Optional
from urllib.parse import urljoin

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import (
    NoSuchElementException,
    ElementNotInteractableException,
    TimeoutException,
)
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC  # noqa: N812


BASE_URL = "https://webscraper.io/"
PAGES = {
    "home": (urljoin(BASE_URL, "test-sites/e-commerce/more/"), False),
    "computers": (
        urljoin(BASE_URL, "test-sites/e-commerce/more/computers"),
        False),
    "laptops": (
        urljoin(BASE_URL, "test-sites/e-commerce/more/computers/laptops"),
        True),
    "tablets": (
        urljoin(BASE_URL, "test-sites/e-commerce/more/computers/tablets"),
        True),
    "phones": (
        urljoin(BASE_URL, "test-sites/e-commerce/more/phones"),
        False),
    "touch": (
        urljoin(BASE_URL, "test-sites/e-commerce/more/phones/touch"),
        True),
}


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int
    additional_info: dict


PRODUCT_FIELDS = [field.name for field in fields(Product)]

logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)8s]: %(message)s",
    handlers=[logging.FileHandler("parse.log"),
              logging.StreamHandler(sys.stdout)],
)


def init_driver(headless: bool = True) -> webdriver.Chrome:
    opts = Options()
    if headless:
        opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--window-size=1920,1080")
    driver = webdriver.Chrome(options=opts)
    driver.implicitly_wait(2)
    return driver


def accept_cookies(driver: webdriver.Chrome) -> None:
    selectors = [
        "button[aria-label='Accept All Cookies']",
        "#accept-cookies",
        "button.cookie-consent-accept",
        "button[title='Accept']",
        "button[aria-label='accept']",
        "button.btn-accept",
    ]
    for sel in selectors:
        try:
            el = driver.find_element(By.CSS_SELECTOR, sel)
            if el.is_displayed():
                try:
                    el.click()
                except Exception:
                    driver.execute_script("arguments[0].click();", el)
                logging.info("Accepted cookies using selector %s", sel)
                time.sleep(0.5)
                return
        except NoSuchElementException:
            continue
    return


def click_load_more_while_exists(
        driver: webdriver.Chrome, max_clicks: int = 200) -> None:
    count = 0
    while count < max_clicks:
        try:
            btn = driver.find_element(
                By.CSS_SELECTOR, ".btn.btn-primary.btn-block")
            if not btn.is_displayed() or not btn.is_enabled():
                break
            driver.execute_script("arguments[0].click();", btn)
            count += 1
            logging.debug("Clicked load-more (%d)", count)
            # give time for new items to load
            time.sleep(0.8)
        except (NoSuchElementException, ElementNotInteractableException):
            break
    if count:
        logging.info("Clicked load-more %d times", count)


def safe_find_text(
        element: WebElement, by: str, selector: str) -> Optional[str]:
    try:
        el = element.find_element(by, selector)
        text = el.text.strip()
        return text if text != "" else None
    except NoSuchElementException:
        return None


def safe_find_attr(
    element: WebElement,
    by: By,
    selector: str,
    attr: str
) -> Optional[str]:
    try:
        el = element.find_element(by, selector)
        attr_value = el.get_attribute(attr)
        return attr_value if attr_value is not None else None
    except NoSuchElementException:
        return None


def parse_product_element(
        element: WebElement, driver: webdriver.Chrome) -> Product:
    title = safe_find_attr(element, By.CLASS_NAME, "title", "title")
    if not title:
        title = safe_find_text(element, By.CLASS_NAME, "title") or ""

    description = safe_find_text(element, By.CLASS_NAME, "description") or ""

    price_text = safe_find_text(element, By.CLASS_NAME, "price") or "0"
    try:
        price = float(price_text.replace("$", "").replace(",", "").strip())
    except Exception:
        price = 0.0

    rating = 0
    try:
        rating_attr = element.find_element(
            By.CSS_SELECTOR, "p[data-rating]").get_attribute("data-rating")
        if rating_attr and rating_attr.isdigit():
            rating = int(rating_attr)
    except NoSuchElementException:
        try:
            stars = element.find_elements(
                By.CSS_SELECTOR, ".ratings .glyphicon-star"
            )
            rating = len(stars)
        except Exception:
            rating = 0

    num_of_reviews = 0
    try:
        rc_text = element.find_element(By.CLASS_NAME, "review-count").text
        num_of_reviews = int(rc_text.split()[0])
    except Exception:
        num_of_reviews = 0

    add_info: Dict[str, str] = {}
    try:
        href = element.find_element(
            By.CLASS_NAME, "title").get_attribute("href")
        if href:
            add_info["url"] = urljoin(BASE_URL, href) \
                if href.startswith("/") else href
    except Exception:
        add_info["url"] = None

    return Product(
        title=title,
        description=description,
        price=price,
        rating=rating,
        num_of_reviews=num_of_reviews,
        additional_info=add_info,
    )


def scrape_with_selenium(
        url: str, click_more: bool, driver: webdriver.Chrome
) -> List[Product]:
    logging.info("Opening %s (click_more=%s)", url, click_more)
    driver.get(url)
    time.sleep(0.6)

    accept_cookies(driver)

    if click_more:
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located(
                    (By.CLASS_NAME, "thumbnail")
                )
            )
        except TimeoutException:
            logging.warning(
                "Timeout waiting for initial product thumbnails on %s", url
            )

        click_load_more_while_exists(driver)

        time.sleep(0.8)
    else:
        try:
            WebDriverWait(
                driver, 6).until(EC.presence_of_all_elements_located
                                 ((By.CLASS_NAME, "thumbnail"))
                                 )
        except TimeoutException:
            logging.warning("Timeout waiting for thumbnails on %s", url)

    try:
        elems = driver.find_elements(By.CLASS_NAME, "thumbnail")
    except Exception:
        elems = []

    products: List[Product] = []
    logging.info("Found %d thumbnail elements on %s", len(elems), url)
    for el in elems:
        try:
            prod = parse_product_element(el, driver)
            products.append(prod)
        except Exception as e:
            logging.exception("Failed to parse product element: %s", e)
            continue

    return products


def write_products_to_csv(products: List[Product], page_name: str) -> None:
    filename = f"{page_name}.csv"
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(PRODUCT_FIELDS)
        for product in products:
            row = [
                product.title,
                product.description,
                f"{product.price:.2f}",
                product.rating,
                product.num_of_reviews,
                product.additional_info,
            ]
            writer.writerow(row)
    logging.info("Wrote %d products to %s", len(products), filename)


def get_all_products() -> None:
    driver = init_driver(headless=True)
    try:
        for page_name, (url, click_more) in PAGES.items():
            try:
                products = scrape_with_selenium(url, click_more, driver)
                write_products_to_csv(products, page_name)
                logging.info(
                    "Page %s done, %d products saved", page_name, len(products)
                )
            except Exception as exc:
                logging.exception(
                    "Failed to process page %s: %s", page_name, exc
                )
    finally:
        try:
            driver.quit()
        except Exception:
            pass


if __name__ == "__main__":
    get_all_products()
