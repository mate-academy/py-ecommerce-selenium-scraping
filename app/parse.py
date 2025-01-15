import csv
import time
from time import sleep
from dataclasses import dataclass, fields
from urllib.parse import urljoin
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium import webdriver

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")

COMPUTERS_URL = urljoin(HOME_URL, "computers/")
PHONES_URL = urljoin(HOME_URL, "phones/")
LAPTOPS_URL = urljoin(COMPUTERS_URL, "laptops")
TABLETS_URL = urljoin(COMPUTERS_URL, "tablets")
TOUCH_URL = urljoin(PHONES_URL, "touch")


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


PRODUCT_FIELDS = [field.name for field in fields(Product)]


def scroll_page(driver: WebDriver) -> None:
    while True:
        try:
            button = driver.find_element(
                By.CLASS_NAME, "ecomerce-items-scroll-more"
            )
            driver.execute_script("arguments[0].scrollIntoView(true);", button)
            button.click()
            time.sleep(1)
        except Exception:
            break


def scrape_page(url: str, with_scroll: bool) -> list[Product]:
    with webdriver.Chrome() as driver:
        driver.get(url)
        sleep(2)

        if with_scroll:
            scroll_page(driver)

        product_elements = driver.find_elements(By.CLASS_NAME, "thumbnail")

        products = []
        for element in product_elements:
            title = element.find_element(By.CLASS_NAME, "title").text
            description = element.find_element(
                By.CLASS_NAME, "description"
            ).text
            price = float(element.find_element(
                By.CLASS_NAME, "price"
            ).text.replace("$", ""))
            rating = len(
                element.find_elements(By.CLASS_NAME, "glyphicon-star")
            )
            num_of_reviews = int(
                element.find_element(
                    By.CLASS_NAME, "ratings"
                ).text.split()[0])

            product = Product(
                title,
                description,
                price,
                rating,
                num_of_reviews
            )
            products.append(product)

    return products


def save_to_csv(products: list[object], filename: str) -> None:
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
