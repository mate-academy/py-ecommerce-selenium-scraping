import csv
import re
import time
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urljoin

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC  # NOQA: N812
from selenium.webdriver.support.ui import WebDriverWait


BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")

PAGES = [
    ("home", HOME_URL, False),
    ("computers", urljoin(
        BASE_URL, "test-sites/e-commerce/more/computers"
    ), False),
    ("laptops", urljoin(
        BASE_URL, "test-sites/e-commerce/more/computers/laptops"
    ), True),
    ("tablets", urljoin(
        BASE_URL, "test-sites/e-commerce/more/computers/tablets"
    ), True),
    ("phones", urljoin(BASE_URL, "test-sites/e-commerce/more/phones"), False),
    ("touch", urljoin(
        BASE_URL, "test-sites/e-commerce/more/phones/touch"
    ), True),
]


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


def _accept_cookies(driver: webdriver.Chrome) -> None:
    """Click accept cookies button when it appears."""
    try:
        cookie_btn = WebDriverWait(driver, 3).until(
            EC.element_to_be_clickable(
                (By.CSS_SELECTOR, "button.acceptCookies")
            )
        )
        cookie_btn.click()
        time.sleep(0.5)
    except Exception:
        pass


def _load_all_products(driver: webdriver.Chrome) -> None:
    """Click 'Load more' button until all products are loaded."""
    while True:
        try:
            more_btn = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable(
                    (
                        By.CSS_SELECTOR,
                        "a.ecomerce-items-scroll-more"
                    )
                )
            )
            driver.execute_script("arguments[0].click();", more_btn)
            time.sleep(0.8)
        except Exception:
            break


def _parse_product(element) -> Product:  # NOQA: ANN001
    """Parse a single product element into a Product dataclass."""
    title_elem = element.find_element(By.CSS_SELECTOR, "a.title")
    title = title_elem.get_attribute("title") or title_elem.text.strip()

    description_elem = element.find_element(By.CSS_SELECTOR, "p.description")
    description = description_elem.text.strip()

    price_text = element.find_element(By.CSS_SELECTOR, "h4.price").text
    price = float(price_text.replace("$", "").strip())

    stars = element.find_elements(By.CSS_SELECTOR, ".ws-icon-star")
    rating = len(stars)

    review_elem = element.find_element(By.CSS_SELECTOR, "p.review-count")
    review_text = review_elem.text
    match = re.search(r"(\d+)\s*reviews?", review_text, re.IGNORECASE)
    num_of_reviews = int(match.group(1)) if match else 0

    return Product(
        title=title,
        description=description,
        price=price,
        rating=rating,
        num_of_reviews=num_of_reviews,
    )


def _scrape_page(
        driver: webdriver.Chrome,
        url: str,
        has_load_more: bool
) -> list[Product]:
    """Scrape all products from a single page."""
    driver.get(url)
    time.sleep(2)

    _accept_cookies(driver)
    time.sleep(0.5)

    product_selector = "div.thumbnail"
    WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, product_selector))
    )
    time.sleep(0.5)

    if has_load_more:
        _load_all_products(driver)
        time.sleep(2)

    product_elements = driver.find_elements(By.CSS_SELECTOR, product_selector)
    products = []
    for elem in product_elements:
        try:
            products.append(_parse_product(elem))
        except Exception:
            continue
    return products


def _save_to_csv(products: list[Product], filename: str) -> None:
    """Save products to a CSV file."""
    with open(
            filename, "w", newline="", encoding="utf-8"
    ) as f:
        writer = csv.writer(f)
        writer.writerow(
            ["title", "description", "price", "rating", "num_of_reviews"]
        )
        for p in products:  # NOQA: VNE001
            writer.writerow([
                p.title,
                p.description,
                str(p.price),
                str(p.rating),
                str(p.num_of_reviews),
            ])


def get_all_products() -> None:
    """Scrape all 6 pages and save products to corresponding CSV files."""
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")

    with webdriver.Chrome(options=options) as driver:
        driver.implicitly_wait(5)

        for page_name, url, has_load_more in PAGES:
            products = _scrape_page(driver, url, has_load_more)
            output_path = Path(page_name).with_suffix(".csv")
            _save_to_csv(products, str(output_path))


if __name__ == "__main__":
    get_all_products()
