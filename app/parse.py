from dataclasses import dataclass, asdict
from typing import List, Optional

import csv
import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.common.exceptions import TimeoutException


BASE_URL = "https://webscraper.io/"


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


def setup_driver(headless: bool = True) -> webdriver.Chrome:
    options = webdriver.ChromeOptions()

    if headless:
        options.add_argument("--headless")

    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    return webdriver.Chrome(options=options)


def accept_cookies(driver: webdriver.Chrome) -> None:
    try:
        cookie_btn = WebDriverWait(driver, 3).until(
            ec.element_to_be_clickable((By.CLASS_NAME, "acceptCookies"))
        )
        cookie_btn.click()
    except TimeoutException:
        pass


def load_all_products(driver: webdriver.Chrome) -> None:
    while True:
        try:
            more_btn = WebDriverWait(driver, 3).until(
                ec.element_to_be_clickable(
                    (By.CLASS_NAME, "ecomerce-items-scroll-more")
                )
            )
            more_btn.click()
            time.sleep(0.5)
        except TimeoutException:
            break


def parse_product(
    element: WebElement
) -> Optional[Product]:

    try:
        title = element.find_element(
            By.CLASS_NAME, "title"
        ).get_attribute("title")

        description = element.find_element(
            By.CLASS_NAME, "description"
        ).text

        price_text = element.find_element(
            By.CLASS_NAME, "price"
        ).text

        price = float(price_text.replace("$", ""))

        rating = len(
            element.find_elements(
                By.CSS_SELECTOR,
                ".ratings .ws-icon-star"
            )
        )

        reviews_text = element.find_element(
            By.CLASS_NAME, "ratings"
        ).find_element(By.TAG_NAME, "p").text

        num_reviews = int(reviews_text.split()[0])

        return Product(
            title,
            description,
            price,
            rating,
            num_reviews,
        )

    except Exception as err:
        print("Parse error:", err)
        return None


def save_to_csv(
    products: List[Product],
    filename: str,
) -> None:

    if not products:
        return

    with open(
        filename,
        "w",
        newline="",
        encoding="utf-8",
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=[
                "title",
                "description",
                "price",
                "rating",
                "num_of_reviews",
            ],
        )

        writer.writeheader()

        for product in products:
            writer.writerow(asdict(product))


def scrape_page(
    driver: webdriver.Chrome,
    url: str,
    output_file: str,
) -> List[Product]:

    driver.get(url)

    accept_cookies(driver)
    load_all_products(driver)

    elements = driver.find_elements(
        By.CLASS_NAME,
        "thumbnail",
    )

    products: List[Product] = []

    for element in elements:
        product = parse_product(element)

        if product:
            products.append(product)

    save_to_csv(products, output_file)

    print(f"Scraped {len(products)} products from {url}")

    return products


def get_all_products() -> None:

    pages = [
        ("https://webscraper.io/test-sites/e-commerce/more", "home.csv"),
        ("https://webscraper.io/test-sites/e-commerce/more/computers", "computers.csv"),
        ("https://webscraper.io/test-sites/e-commerce/more/computers/laptops", "laptops.csv"),
        ("https://webscraper.io/test-sites/e-commerce/more/computers/tablets", "tablets.csv"),
        ("https://webscraper.io/test-sites/e-commerce/more/phones", "phones.csv"),
        ("https://webscraper.io/test-sites/e-commerce/more/phones/touch", "touch.csv"),
    ]

    driver = setup_driver()

    try:
        for url, filename in pages:
            scrape_page(driver, url, filename)
    finally:
        driver.quit()


if __name__ == "__main__":
    get_all_products()
