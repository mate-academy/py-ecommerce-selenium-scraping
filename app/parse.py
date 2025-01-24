import csv
from dataclasses import dataclass, fields
import time
from urllib.parse import urljoin
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium import webdriver
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")
COMPUTERS_URL = urljoin(HOME_URL, "computers/")
LAPTOPS_URL = urljoin(COMPUTERS_URL, "laptops")
TABLETS_URL = urljoin(COMPUTERS_URL, "tablets")
PHONES_URL = urljoin(HOME_URL, "phones/")
TOUCH_URL = urljoin(PHONES_URL, "touch")

_driver: WebDriver | None = None


def get_driver():
    return _driver


def set_driver(new_driver):
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


def parse_single_product(product: WebDriver) -> Product:
    return Product(
        title=product.find_element(By.CLASS_NAME, "title").get_attribute(
            "title"
        ),
        description=product.find_element(By.CLASS_NAME, "description").text,
        price=float(
            product.find_element(By.CLASS_NAME, "price").text.replace("$", "")
        ),
        rating=len(product.find_elements(By.CLASS_NAME, "ws-icon-star")),
        num_of_reviews=int(
            product.find_element(By.CLASS_NAME, "ratings").text.split()[0]
        ),
    )


def scroll_page(driver: WebDriver) -> None:
    last_count = 0
    while True:
        try:
            product_elements = driver.find_elements(By.CLASS_NAME, "thumbnail")
            current_count = len(product_elements)

            if current_count == last_count:
                print("No more products to load.")
                break

            last_count = current_count

            button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CLASS_NAME, "ecomerce-items-scroll-more"))
            )

            driver.execute_script("arguments[0].click();", button)
            print(f"Clicked 'Load More', current count: {current_count}")

            WebDriverWait(driver, 10).until(
                lambda d: len(d.find_elements(By.CLASS_NAME, "thumbnail")) > current_count
            )
            print(f"New products loaded, count: {len(driver.find_elements(By.CLASS_NAME, 'thumbnail'))}")

        except Exception as e:
            print(f"Scrolling finished or error occurred: {e}")
            break


def scrape_page(url: str, with_scroll: bool) -> list[Product]:
    with webdriver.Chrome() as driver:
        driver.get(url)
        time.sleep(2)

        if with_scroll:
            scroll_page(driver)

        product_elements = driver.find_elements(By.CLASS_NAME, "thumbnail")

        products = [parse_single_product(element) for element in product_elements]

    return products


def save_to_csv(products: list[Product], filename: str) -> None:
    with open(filename, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(PRODUCT_FIELDS)
        for product in products:
            writer.writerow(
                [getattr(product, field) for field in PRODUCT_FIELDS]
            )


def get_all_products() -> None:
    urls = {
        "home": HOME_URL,
        "computers": COMPUTERS_URL,
        "laptops": LAPTOPS_URL,
        "tablets": TABLETS_URL,
        "phones": PHONES_URL,
        "touch": TOUCH_URL
    }

    for page_name, url in urls.items():
        print(f"Scraping {page_name} page...")
        with_scroll = page_name in {"laptops", "tablets", "touch"}
        products = scrape_page(url, with_scroll=with_scroll)
        save_to_csv(products, f"{page_name}.csv")
        print(f"Saved {len(products)} products to {page_name}.csv")


if __name__ == "__main__":
    get_all_products()