import csv
import time
from dataclasses import dataclass, fields
from urllib.parse import urljoin
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC  # noqa: N812
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from typing import Any
from tqdm import tqdm as tqdm_cls


try:
    from tqdm import tqdm
except ImportError:
    def tqdm(iterable: Any, *args: Any, **kwargs: Any) -> tqdm_cls:
        return iterable

BASE_URL = "https://webscraper.io"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


def parse_single_product(element: WebElement) -> Product:
    """Parses product data fields safely handling missing layout elements."""
    title = element.find_element(
        By.CSS_SELECTOR,
        "a.title"
    ).get_attribute("title").strip()
    if not title:
        title = element.find_element(By.CSS_SELECTOR, "a.title").text.strip()

    description = element.find_element(
        By.CLASS_NAME,
        "description"
    ).text.strip()

    price_text = element.find_element(By.CLASS_NAME, "price").text
    price = float(price_text.replace("$", "").replace(",", "").strip())

    try:
        rating_elem = element.find_element(
            By.CSS_SELECTOR,
            ".ratings p[data-rating]"
        )
        rating = int(rating_elem.get_attribute("data-rating"))
    except Exception:
        try:
            stars = element.find_elements(
                By.CSS_SELECTOR,
                ".ratings [class*='star']"
            )
            rating = len(stars)
        except Exception:
            rating = 0

    reviews_text = element.find_element(
        By.CSS_SELECTOR,
        ".ratings p.review-count, .ratings p.pull-right"
    ).text
    num_of_reviews = int(reviews_text.split()[0])

    return Product(title, description, price, rating, num_of_reviews)


def handle_cookies(driver: WebDriver) -> None:
    """Dismisses cookie banners or modals that block hidden element targets."""
    try:
        cookie_button = WebDriverWait(driver, 2).until(
            EC.element_to_be_clickable((
                By.XPATH,
                "//button[contains(text(), 'Accept') "
                "or contains(text(), 'Cookie')]"
            ))
        )
        cookie_button.click()
        time.sleep(0.5)
    except TimeoutException:
        pass


def scrape_page(
        driver: WebDriver,
        url: str,
        has_more_button: bool = False
) -> list[Product]:
    """Universal pagination page worker tracking
    dynamic layout tree updates."""
    driver.get(url)
    handle_cookies(driver)

    if has_more_button:
        while True:
            try:
                more_button = WebDriverWait(driver, 3).until(
                    EC.presence_of_element_located((
                        By.CSS_SELECTOR,
                        "a.ecom-btn-more, .ecom-btn-more, a.btn-primary"
                    ))
                )

                if (
                        "display: none" in more_button.get_attribute("style")
                        or not more_button.is_displayed()
                ):
                    break

                driver.execute_script(
                    "arguments[0].scrollIntoView({block: 'center'});",
                    more_button
                )
                time.sleep(0.3)

                driver.execute_script("arguments[0].click();", more_button)

                time.sleep(1.0)

            except (TimeoutException, NoSuchElementException):
                break
            except Exception:
                break

    product_elements = driver.find_elements(
        By.CSS_SELECTOR,
        ".thumbnail, div.thumbnail"
    )
    products = []

    page_identifier = url.rstrip("/").split("/")[-1] or "home"
    for elem in tqdm(
            product_elements,
            desc=f"Scraping '{page_identifier}' category"
    ):
        try:
            products.append(parse_single_product(elem))
        except Exception:
            continue

    return products


def save_to_csv(products: list[Product], filename: str) -> None:
    field_names = [f.name for f in fields(Product)]
    with open(filename, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=field_names)
        writer.writeheader()
        for prod in products:
            writer.writerow(prod.__dict__)


def get_all_products() -> None:
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--window-size=1920,1080")

    chrome_options.add_argument(
        "--disable-blink-features=AutomationControlled"
    )
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--remote-debugging-port=9222")

    driver = webdriver.Chrome(options=chrome_options)

    pages = [
        {"name": "home", "url": HOME_URL, "pagination": False},
        {
            "name": "computers",
            "url": urljoin(HOME_URL, "computers"),
            "pagination": False
        },
        {
            "name": "laptops",
            "url": urljoin(HOME_URL, "computers/laptops"),
            "pagination": True
        },
        {
            "name": "tablets",
            "url": urljoin(HOME_URL, "computers/tablets"),
            "pagination": True
        },
        {
            "name": "phones",
            "url": urljoin(HOME_URL, "phones"),
            "pagination": False
        },
        {
            "name": "touch",
            "url": urljoin(HOME_URL, "phones/touch"),
            "pagination": True
        },
    ]

    try:
        for page in pages:
            products = scrape_page(
                driver,
                page["url"],
                has_more_button=page["pagination"]
            )
            save_to_csv(products, f"{page["name"]}.csv")
    finally:
        driver.quit()


if __name__ == "__main__":
    get_all_products()
