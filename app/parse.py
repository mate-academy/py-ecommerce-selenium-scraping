import csv
import time
from dataclasses import dataclass
from urllib.parse import urljoin

from selenium import webdriver
from selenium.common.exceptions import (
    ElementClickInterceptedException,
    NoSuchElementException,
    StaleElementReferenceException,
)
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.remote.webelement import WebElement


BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")

options = Options()
driver = webdriver.Chrome(options=options)


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


def parse_product(element: WebElement) -> Product:
    title = element.find_element(By.CLASS_NAME, "title").get_attribute("title")
    description = element.find_element(
        By.CLASS_NAME, "description"
    ).text.strip()

    price = float(
        element.find_element(By.CLASS_NAME, "price").text.replace("$", "")
    )
    rating = len(
        element.find_elements(By.CSS_SELECTOR, ".ratings .ws-icon-star")
    )
    num_of_reviews = int(
        element.find_element(By.CLASS_NAME, "review-count")
        .text.strip()
        .split()[0]
    )

    return Product(title, description, price, rating, num_of_reviews)


def parse_page(url: str) -> list[Product]:
    driver.get(url)
    products = []

    try:
        accept_btn = WebDriverWait(driver, 1).until(
            expected_conditions.element_to_be_clickable(
                (
                    By.XPATH,
                    "//button[contains(., 'Accept') or contains(., 'OK')]",
                )
            )
        )
        accept_btn.click()
    except Exception:
        pass

    WebDriverWait(driver, 3).until(
        expected_conditions.presence_of_element_located(
            (By.CLASS_NAME, "thumbnail")
        )
    )

    while True:
        elements = driver.find_elements(By.CLASS_NAME, "thumbnail")
        for element in elements[len(products) :]:
            products.append(parse_product(element))

        try:
            load_more = driver.find_element(
                By.CLASS_NAME, "ecomerce-items-scroll-more"
            )

            if not load_more.is_displayed():
                break

            driver.execute_script(
                "arguments[0].scrollIntoView("
                "{behavior: 'smooth', block: 'center'}"
                ");",
                load_more,
            )
            time.sleep(0.1)

            try:
                load_more.click()
            except (
                ElementClickInterceptedException,
                StaleElementReferenceException,
            ):
                time.sleep(0.1)
                load_more = driver.find_element(
                    By.CLASS_NAME, "ecomerce-items-scroll-more"
                )
                load_more.click()

            WebDriverWait(driver, 10).until(
                lambda driver_: len(
                    driver_.find_elements(By.CLASS_NAME, "thumbnail")
                )
                > len(products)
            )
        except NoSuchElementException:
            break

    return products


def save_to_csv(products: list[Product], filename: str) -> None:
    with open(filename, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(
            ["title", "description", "price", "rating", "num_of_reviews"]
        )
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
    pages = {
        "home": HOME_URL,
        "computers": urljoin(HOME_URL, "computers"),
        "laptops": urljoin(HOME_URL, "computers/laptops"),
        "tablets": urljoin(HOME_URL, "computers/tablets"),
        "phones": urljoin(HOME_URL, "phones"),
        "touch": urljoin(HOME_URL, "phones/touch"),
    }

    for name, url in pages.items():
        print(f"Scraping: {name} -> {url}")
        products = parse_page(url)
        save_to_csv(products, f"{name}.csv")
        print(f"Saved {len(products)} products to {name}.csv")


if __name__ == "__main__":
    get_all_products()
