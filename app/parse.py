from __future__ import annotations

import csv
import time
from dataclasses import dataclass, asdict
from dataclasses import fields as dc_fields

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.common.exceptions import TimeoutException
from typing import TypeVar


T = TypeVar("T")
try:
    # Optional nice progress bars
    from tqdm import tqdm
except Exception:  # pragma: no cover
    def tqdm(iterable: T, **kwargs) -> T:
        return iterable


# ──────────────────────────────────────────────────────────────────────────────
# Data model
# Matches the e-commerce test site card info:
#   title, price, description, rating (0-5), reviews (int), url (product link)
# If your local template differs, adjust fields here;
# everything else will adapt.
# ──────────────────────────────────────────────────────────────────────────────
@dataclass
class Product:
    title: str = "title"
    description: str = "description"
    price: float = 0.0
    rating: int = 0
    num_of_reviews: int = 0
    # url: str = "url"


# ──────────────────────────────────────────────────────────────────────────────
# Driver / utils
# ──────────────────────────────────────────────────────────────────────────────
def make_driver(headless: bool = True) -> webdriver.Chrome:
    opts = Options()
    if headless:
        # “New” headless mode (Chrome 109+) behaves better
        opts.add_argument("--headless=new")
    # Keep things stable in CI
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--window-size=1920,1080")
    opts.add_argument("--disable-blink-features=AutomationControlled")
    driver = webdriver.Chrome(options=opts)
    driver.set_page_load_timeout(30)
    return driver


def accept_cookies_if_present(
        driver: webdriver.Chrome,
        timeout: int = 5
) -> None:
    """Click cookie banner if it appears; supports a few common selectors."""
    selectors = [
        # webscraper.io uses an Onetrust-like consent on occasion
        (By.ID, "onetrust-accept-btn-handler"),
        (
            By.CSS_SELECTOR,
            "#onetrust-accept-btn-handler, .onetrust-accept-btn-handler"
        ),
        # Some mirrors/sites
        (By.CSS_SELECTOR, "button#accept-cookies, button.cookie-accept"),
    ]
    end = time.time() + timeout
    for (by, sel) in selectors:
        try:
            WebDriverWait(driver, max(0, int(end - time.time()))).until(
                ec.element_to_be_clickable((by, sel))
            ).click()
            time.sleep(0.2)
            return
        except Exception:
            pass  # Try next selector


def click_more_until_exhausted(
        driver: webdriver.Chrome,
        max_clicks: int = 400
) -> None:
    """
    Click the 'More' button (class ecomerce-items-scroll-more) until:
      - the button disappears,
      - the button becomes disabled,
      - or no new items appear after a click.
    Works for the /e-commerce/more site variant.
    """
    # Accept both misspelled and (just in case) correctly spelled variants
    btn_sel = "a.ecomerce-items-scroll-more, a.ecommerce-items-scroll-more"

    def is_disabled(btn: WebElement) -> bool:
        cls = (btn.get_attribute("class") or "").lower()
        aria = (btn.get_attribute("aria-disabled") or "").lower()
        disabled = btn.get_attribute("disabled")
        return "disabled" in cls or aria in ("true", "1") or bool(disabled)

    last_count = -1
    for _ in range(max_clicks):
        # Current number of cards
        cards = driver.find_elements(By.CSS_SELECTOR, ".thumbnail")
        count_before = len(cards)

        # If nothing changed over the last loop, we may be done
        if count_before == last_count:
            btns = driver.find_elements(By.CSS_SELECTOR, btn_sel)
            if not btns:
                break
            if is_disabled(btns[0]):
                break
        last_count = count_before

        # Find the button
        btns = driver.find_elements(By.CSS_SELECTOR, btn_sel)
        if not btns:
            break
        btn = btns[0]
        if is_disabled(btn):
            break

        # Scroll into view & click
        try:
            driver.execute_script(
                "arguments[0].scrollIntoView({block:'center'});", btn
            )
            time.sleep(0.15)
            try:
                btn.click()
            except Exception:
                # Fallback to JS click
                driver.execute_script("arguments[0].click();", btn)
        except Exception:
            break

        # Wait for more items to load (count must increase)
        try:
            WebDriverWait(driver, 10).until(
                lambda d: len(
                    d.find_elements(By.CSS_SELECTOR, ".thumbnail")
                ) > count_before
            )
        except TimeoutException:
            # No increase → likely exhausted
            break

        # Small settle time (images/layout)
        time.sleep(0.2)


def _default_for_type(type_annotation: type) -> object:
    try:
        origin = type_annotation.__origin__
    except AttributeError:
        origin = None
    if type_annotation in (int, float) or origin in (int, float):
        return 0
    if type_annotation in (bool,) or origin is bool:
        return False
    return ""


def create_product(data: dict) -> Product:
    """
    Safe Product constructor:
    - Only uses fields actually present on the current Product dataclass
    - Fills ANY missing required fields with sensible defaults
    This guarantees no 'missing positional argument' errors.
    """
    values = {}
    for field in dc_fields(Product):
        values[field.name] = data.get(
            field.name, _default_for_type(field.type)
        )
    return Product(**values)


def parse_product_cards(driver: webdriver) -> list[Product]:
    products = []
    cards = driver.find_elements(By.CSS_SELECTOR, ".thumbnail")
    for el in cards:
        # Title + URL
        try:
            title_el = el.find_element(By.CSS_SELECTOR, ".title")
            title = title_el.get_attribute("title") or title_el.text.strip()
        except Exception:
            title = ""

        # Price
        try:
            price_text = el.find_element(
                By.CSS_SELECTOR, ".price"
            ).text.strip()
            # remove $, commas, spaces and convert to float
            price = float(price_text.replace("$", "").replace(",", "").strip())
        except Exception:
            price = 0.0

        # Description
        try:
            description = el.find_element(
                By.CSS_SELECTOR, ".description"
            ).text.strip()
        except Exception:
            description = ""

        # Rating = star count
        try:
            stars = el.find_elements(
                By.CSS_SELECTOR,
                "p .ws-icon.ws-icon-star"
            )
            if stars:
                rating = len(stars)
            else:
                rating_p = el.find_element(By.CSS_SELECTOR, "p[data-rating]")
                stars = rating_p.find_elements(
                    By.CSS_SELECTOR,
                    ".ws-icon.ws-icon-star"
                )
                rating = len(stars) if stars else int(
                    rating_p.get_attribute("data-rating") or 0
                )
        except Exception:
            rating = 0

        # Reviews
        try:
            reviews_span = el.find_element(
                By.CSS_SELECTOR,
                "p.review-count.float-end span[itemprop='reviewCount']"
            )
            reviews = int(reviews_span.text.strip())
        except Exception:
            reviews = 0

        # --- SAFE INSTANTIATION ---
        data = {
            "title": title or "",
            "description": description or "",
            "price": price if price is not None else "",
            "rating": rating,
            "num_of_reviews": reviews,
            # "url": url or "",          # will be ignored if not in dataclass
        }
        products.append(create_product(data))
    return products


def write_csv(path: str, rows: list[Product]) -> None:
    rows = list(rows)
    headers = list(Product.__dataclass_fields__.keys())
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        for _ in rows:
            row = asdict(_)
            writer.writerow({k: row.get(k, "") for k in headers})


# ──────────────────────────────────────────────────────────────────────────────
# Main orchestration
# ──────────────────────────────────────────────────────────────────────────────
def get_all_products(
        base: str = "https://webscraper.io/test-sites/e-commerce/more",
        headless: bool = True,
        out_dir: str = ".",
) -> None:
    """
    Scrape all required pages and save CSVs:
      - home.csv               (3 random products)
      - computers.csv          (3 random computers)
      - laptops.csv            (117 laptops; 'Show more' pagination)
      - tablets.csv            (21 tablets; 'Show more' pagination)
      - phones.csv             (3 random phones)
      - touch.csv              (9 touch phones; 'Show more' pagination)
    """
    pages = {
        "home": f"{base}",
        "computers": f"{base}/computers",
        "laptops": f"{base}/computers/laptops",
        "tablets": f"{base}/computers/tablets",
        "phones": f"{base}/phones",
        "touch": f"{base}/phones/touch",
    }

    driver = make_driver(headless=headless)
    try:
        for page_name, url in tqdm(pages.items(), desc="Scraping pages"):
            driver.get(url)
            accept_cookies_if_present(driver)

            # Wait until product grid is visible
            try:
                WebDriverWait(driver, 15).until(
                    ec.presence_of_all_elements_located(
                        (By.CSS_SELECTOR, ".thumbnail")
                    )
                )
            except TimeoutException:
                # Try a short extra wait if network hiccups
                time.sleep(1)

            # Handle “Show more” pages
            if page_name in {"laptops", "tablets", "touch"}:
                click_more_until_exhausted(driver)

            products = parse_product_cards(driver)
            # Write per-page CSV
            csv_path = f"{out_dir}/{page_name}.csv"
            write_csv(csv_path, products)

    finally:
        driver.quit()


# For manual/local run
if __name__ == "__main__":
    # Headless by default; outputs CSVs into current folder
    get_all_products(headless=True, out_dir=".")
