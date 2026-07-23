import csv
import time
from dataclasses import dataclass, fields, astuple
from urllib.parse import urljoin

from selenium import webdriver
from selenium.common.exceptions import (
    NoSuchElementException,
    TimeoutException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.wait import WebDriverWait

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")

PAGES_URL = {
    "home": HOME_URL,
    "computers": f"{HOME_URL}computers",
    "laptops": f"{HOME_URL}computers/laptops",
    "tablets": f"{HOME_URL}computers/tablets",
    "phones": f"{HOME_URL}phones",
    "touch": f"{HOME_URL}phones/touch",
}


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


def init_driver(headless: bool = True) -> webdriver.Chrome:
    options = Options()
    options.headless = headless
    return webdriver.Chrome(options=options)


def extract_product(product: webdriver) -> Product:
    return Product(
        title=product.find_element(
            By.CSS_SELECTOR,
            "a.title"
        ).get_attribute("title"),
        description=product.find_element(
            By.CSS_SELECTOR,
            "p.description"
        ).text,
        price=float(product.find_element(
            By.CSS_SELECTOR,
            "h4.price"
        ).text.replace("$", "")),
        rating=len(product.find_elements(
            By.CSS_SELECTOR,
            "span.ws-icon-star")
        ),
        num_of_reviews=int(product.find_element(
            By.CSS_SELECTOR,
            "p.review-count"
        ).text.split()[0]),
    )


def parse_page(driver: webdriver.Chrome, url: str) -> list[Product]:
    driver.get(url)
    accept_cookies(driver)

    while True:
        try:
            button = WebDriverWait(driver, 5).until(
                ec.element_to_be_clickable((
                    By.CSS_SELECTOR,
                    ".ecomerce-items-scroll-more"
                ))
            )
            if "display: none" in button.get_attribute("style"):
                raise NoSuchElementException
            driver.execute_script("arguments[0].click();", button)
            time.sleep(0.5)
        except (NoSuchElementException, TimeoutException):
            break

    WebDriverWait(driver, 5).until(
        ec.presence_of_all_elements_located((
            By.CSS_SELECTOR, "div.card-body"
        ))
    )

    products = [extract_product(product) for product in driver.find_elements(
        By.CSS_SELECTOR,
        "div.card-body"
    )]

    print(f"Total product elements found for {url}: {len(products)}")

    return products


def write_to_csv(products: list[Product], file_name: str) -> None:
    with open(f"{file_name}.csv", "w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        writer.writerow([field.name for field in fields(Product)])
        writer.writerows([astuple(product) for product in products])


def accept_cookies(driver: webdriver.Chrome) -> None:
    try:
        cookies_btn = driver.find_element(By.CLASS_NAME, "acceptCookies")
        if cookies_btn.is_displayed():
            cookies_btn.click()
    except NoSuchElementException:
        pass


def get_all_products() -> None:
    driver = init_driver()
    try:
        for file_name, url in PAGES_URL.items():
            print(f"Scraping category: {file_name}")
            products = parse_page(driver, url)
            write_to_csv(products, file_name)
            print(f"Saved {len(products)} products to {file_name}.csv")
    finally:
        driver.quit()


if __name__ == "__main__":
    get_all_products()
