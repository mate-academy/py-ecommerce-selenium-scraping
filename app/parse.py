import csv
import time
from dataclasses import dataclass
from urllib.parse import urljoin

from selenium import webdriver
from selenium.common import NoSuchElementException, TimeoutException
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

BASE_URL = "https://webscraper.io/"
URLS_TO_PARSE = {
    "home": "test-sites/e-commerce/more/",
    "laptops": "test-sites/e-commerce/more/computers/laptops",
    "tablets": "test-sites/e-commerce/more/computers/tablets",
    "phones": "test-sites/e-commerce/more/phones",
    "touch": "test-sites/e-commerce/more/phones/touch",
    "computers": "test-sites/e-commerce/more/computers",
}


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


def parse_product(elem: WebElement) -> Product:
    return Product(
        title=elem.find_element(
            By.CSS_SELECTOR,
            "h4 > a"
        ).get_attribute("title"),
        description=elem.find_element(
            By.CSS_SELECTOR,
            "p.description"
        ).text,
        price=float(elem.find_element(
            By.CSS_SELECTOR,
            "h4.float-end"
        ).text.replace("$", "")),
        rating=len(elem.find_elements(
            By.CSS_SELECTOR,
            "span.ws-icon-star")
        ),
        num_of_reviews=int(
            elem.find_element(
                By.CSS_SELECTOR,
                "p.review-count"
            ).text.split()[0]),
    )


def handle_cookie_banner(driver: WebDriver) -> None:
    try:
        accept_button = driver.find_element(
            By.CSS_SELECTOR,
            "button.acceptCookies"
        )
        accept_button.click()
    except NoSuchElementException:
        pass


def scrape_product_page(driver: WebDriver, url: str) -> list[Product]:
    driver.get(urljoin(BASE_URL, url))
    handle_cookie_banner(driver)

    while True:
        try:
            more_button = WebDriverWait(driver, 3).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "a.ecomerce-items-scroll-more"))
            )
            more_button.click()
            time.sleep(0.2)
        except TimeoutException:
            break
        except NoSuchElementException:
            break

    products = driver.find_elements(By.CSS_SELECTOR, ".product-wrapper")
    return [parse_product(product) for product in products]


def save_products_to_csv(filename: str, products: list[Product]) -> None:
    with open(f"{filename}.csv", "w", encoding="utf-8", newline="") as file:
        csv_writer = csv.writer(file)
        csv_writer.writerow(
            ["title", "description", "price", "rating", "num_of_reviews"]
        )
        for product in products:
            csv_writer.writerow(
                [
                    product.title,
                    product.description,
                    product.price,
                    product.rating,
                    product.num_of_reviews,
                ]
            )


def get_all_products() -> None:
    driver = webdriver.Chrome()

    for filename, url in URLS_TO_PARSE.items():
        print(f"Scraping {BASE_URL}: {filename}")
        products = scrape_product_page(driver, url)
        save_products_to_csv(filename, products)

    driver.quit()


if __name__ == "__main__":
    get_all_products()
