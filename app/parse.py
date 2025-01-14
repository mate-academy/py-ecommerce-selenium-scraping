import csv
import logging
from urllib.parse import urljoin
from dataclasses import asdict
from dataclasses import dataclass

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from tqdm import tqdm

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


def parse_single_product(product: WebElement) -> Product:
    return Product(
        title=product.find_element(By.CLASS_NAME, "title").get_attribute(
            "title"
        ),
        description=product.find_element(
            By.CLASS_NAME, "description"
        ).text.strip(),
        price=float(
            product.find_element(By.CLASS_NAME, "price").text.strip()[1:]
        ),
        rating=len(product.find_elements(By.CLASS_NAME, "ws-icon-star")),
        num_of_reviews=int(
            product.find_element(By.CLASS_NAME, "ratings").text.split()[0]
        ),
    )


def scrape_page(driver: webdriver.Chrome, url: str, product_page: str) -> list[Product]:
    driver.get(url)
    try:
        WebDriverWait(driver, 1).until(
            expected_conditions.element_to_be_clickable(
                (By.ID, "accept-cookies")
            )
        ).click()
    except TimeoutException:  # noqa E722
        pass

    while True:
        try:
            more_button = WebDriverWait(driver, 3).until(
                expected_conditions.element_to_be_clickable(
                    (By.CLASS_NAME, "btn.btn-primary")
                )
            )
            ActionChains(driver).move_to_element(more_button).click().perform()
        except TimeoutException: # noqa E722
            break

    products = []
    product_elements = driver.find_elements(By.CLASS_NAME, "thumbnail")
    for product in tqdm(product_elements, desc=f"Parsing poducts from {product_page} page"):
        products.append(parse_single_product(product))

    return products


def save_to_csv(filename: str, products: list[Product]) -> None:
    with open(filename, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=asdict(products[0]).keys())
        writer.writeheader()
        if products:
            for product in products:
                writer.writerow(asdict(product))


def get_all_products() -> None:
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox") # fixes ubuntu crash

    driver = webdriver.Chrome(options=options)
    pages = {
        "home.csv": HOME_URL,
        "computers.csv": urljoin(HOME_URL, "computers"),
        "laptops.csv": urljoin(HOME_URL, "computers/laptops"),
        "tablets.csv": urljoin(HOME_URL, "computers/tablets"),
        "phones.csv": urljoin(HOME_URL, "phones"),
        "touch.csv": urljoin(HOME_URL, "phones/touch"),
    }

    try:
        for filename, url in tqdm(pages.items(), desc="Scraping Pages"):
            products = scrape_page(driver, url, filename.split(".")[0])
            save_to_csv(filename, products)
    finally:
        driver.quit()


if __name__ == "__main__":
    get_all_products()
