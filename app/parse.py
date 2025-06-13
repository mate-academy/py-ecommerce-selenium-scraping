import csv
import time
from dataclasses import dataclass, asdict

from typing import List
from urllib.parse import urljoin
from selenium import webdriver
from selenium.common import TimeoutException
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC  # noqa: N812


BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


PAGES = {
    "home": HOME_URL,
    "computers": urljoin(HOME_URL, "computers"),
    "laptops": urljoin(HOME_URL, "computers/laptops"),
    "tablets": urljoin(HOME_URL, "computers/tablets"),
    "phones": urljoin(HOME_URL, "phones"),
    "touch": urljoin(HOME_URL, "phones/touch")
}

MORE_BUTTON_CATEGORIES = {"laptops", "tablets", "touch"}


def click_all_more_buttons(driver: WebDriver) -> None:
    try:
        cookie_btn = WebDriverWait(driver, 2).until(
            EC.element_to_be_clickable((By.CLASS_NAME, "acceptCookies"))
        )
        cookie_btn.click()
        time.sleep(0.5)
    except TimeoutException:
        pass
    while True:
        try:
            old_count = len(driver.find_elements(By.CLASS_NAME, "thumbnail"))
            more_btn = WebDriverWait(driver, 2).until(
                EC.element_to_be_clickable((By.CLASS_NAME, "btn-primary"))
            )
            more_btn.click()

            WebDriverWait(driver, 5).until(
                lambda d: len(
                    d.find_elements(By.CLASS_NAME, "thumbnail")
                ) > old_count
            )
        except TimeoutException:
            break


def scrape_page(
        driver: WebDriver,
        url: str,
        load_all: bool = False
) -> List[Product]:
    driver.get(url)
    time.sleep(1)

    if load_all:
        click_all_more_buttons(driver)

    products = []
    product_elements = driver.find_elements(By.CLASS_NAME, "thumbnail")

    for elem in product_elements:
        title = (elem.find_element(By.CLASS_NAME, "title")
                 .get_attribute("title"))
        description = elem.find_element(By.CLASS_NAME, "description").text
        price_text = (elem.find_element(By.CLASS_NAME, "price")
                      .text.replace("$", "").strip())
        price = float(price_text)

        rating = len(elem.find_elements(
            By.CSS_SELECTOR,
            ".ws-icon.ws-icon-star"
        ))

        num_of_reviews = int(elem.find_element(
            By.CSS_SELECTOR,
            '[itemprop="reviewCount"]'
        ).text)
        products.append(Product(
            title,
            description,
            price,
            rating,
            num_of_reviews
        ))

    return products


def save_to_csv(filename: str, products: List[Product]) -> None:
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=Product.__annotations__.keys())
        writer.writeheader()
        for product in products:
            writer.writerow(asdict(product))


def get_all_products() -> None:
    options = Options()
    options.add_argument("--headless")
    driver = webdriver.Chrome(options=options)

    try:
        for name, url in PAGES.items():
            load_all = name in MORE_BUTTON_CATEGORIES
            products = scrape_page(driver, url, load_all=load_all)
            save_to_csv(f"{name}.csv", products)
            print(f"Saved {len(products)} products to {name}.csv")
    finally:
        driver.quit()


if __name__ == "__main__":
    get_all_products()
