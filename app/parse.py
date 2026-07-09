import csv
from dataclasses import dataclass, fields
import time
from urllib.parse import urljoin

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from webdriver_manager.chrome import ChromeDriverManager
from tqdm import tqdm

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")

PAGES_CONFIG = [
    ("home", "", False),
    ("computers", "computers", False),
    ("laptops", "computers/laptops", True),
    ("tablets", "computers/tablets", True),
    ("phones", "phones", False),
    ("touch", "phones/touch", True),
]


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


def get_driver() -> webdriver.Chrome:
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--log-level=3")
    options.add_argument("--disable-blink-features=AutomationControlled")

    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)


def parse_single_page(
    driver: webdriver.Chrome, page_url: str, has_more_button: bool
) -> list[Product]:
    driver.get(page_url)

    try:
        accept = WebDriverWait(driver, 5).until(
            ec.element_to_be_clickable((By.CSS_SELECTOR, ".t-acceptAllButton"))
        )
        accept.click()
    except Exception:
        pass

    WebDriverWait(driver, 10).until(
        ec.presence_of_element_located((By.CSS_SELECTOR, ".thumbnail"))
    )

    if has_more_button:
        while True:
            try:
                buttons = driver.find_elements(
                    By.CSS_SELECTOR, "a.ecomerce-items-scroll-more"
                )

                if not buttons:
                    time.sleep(2)
                    buttons = driver.find_elements(
                        By.CSS_SELECTOR, "a.ecomerce-items-scroll-more"
                    )
                    if not buttons:
                        break

                current = len(
                    driver.find_elements(By.CSS_SELECTOR, ".thumbnail")
                )
                print(current)
                driver.execute_script("arguments[0].click();", buttons[0])
                WebDriverWait(driver, 10).until(
                    lambda d: len(
                        d.find_elements(By.CSS_SELECTOR, ".thumbnail")
                    )
                    > current
                )
            except Exception as e:
                print(e)
                break

    time.sleep(1.5)

    products = []
    product_elements = driver.find_elements(By.CSS_SELECTOR, ".thumbnail")

    for element in product_elements:
        title = (
            element.find_element(By.CSS_SELECTOR, ".title")
            .get_attribute("title")
            .strip()
        )
        description = element.find_element(
            By.CSS_SELECTOR, ".description"
        ).text.strip()

        price_text = (
            element.find_element(By.CSS_SELECTOR, ".price")
            .text.replace("$", "")
            .strip()
        )
        price = float(price_text)

        reviews_text = element.find_element(
            By.CSS_SELECTOR, ".ratings p.review-count"
        ).text
        num_of_reviews = int(reviews_text.split()[0].strip())

        stars = element.find_elements(
            By.CSS_SELECTOR, ".ratings span.ws-icon-star"
        )
        rating = len(stars)

        products.append(
            Product(
                title=title,
                description=description,
                price=price,
                rating=rating,
                num_of_reviews=num_of_reviews,
            )
        )

    return products


def save_to_csv(filename: str, products: list[Product]) -> None:
    field_names = [f.name for f in fields(Product)]

    with open(f"{filename}.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(field_names)

        for product in products:
            writer.writerow(
                [
                    product.title,
                    product.description,
                    product.price,
                    product.rating,
                    product.num_of_reviews,
                ]
            )


def get_all_products() -> None:
    driver = get_driver()
    try:
        for filename, path, has_more_button in tqdm(
            PAGES_CONFIG, desc="Scraping pages"
        ):
            page_url = urljoin(HOME_URL, path)
            products = parse_single_page(driver, page_url, has_more_button)
            save_to_csv(filename, products)
    finally:
        driver.quit()


if __name__ == "__main__":
    get_all_products()
