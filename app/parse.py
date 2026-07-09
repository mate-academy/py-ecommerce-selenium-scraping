import csv
import time
from dataclasses import dataclass, fields
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.common.exceptions import (
    TimeoutException,
    ElementClickInterceptedException
)
from tqdm import tqdm

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")


PAGES_CONFIG = {
    "home": HOME_URL,
    "computers": urljoin(HOME_URL, "computers"),
    "laptops": urljoin(HOME_URL, "computers/laptops"),
    "tablets": urljoin(HOME_URL, "computers/tablets"),
    "phones": urljoin(HOME_URL, "phones"),
    "touch": urljoin(HOME_URL, "phones/touch"),
}


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


def get_driver() -> webdriver.Chrome:
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--logging-level=3")
    return webdriver.Chrome(options=chrome_options)


def accept_cookies(driver: webdriver.Chrome) -> None:
    try:
        cookie_btn = WebDriverWait(driver, 3).until(
            ec.element_to_be_clickable((By.CLASS_NAME, "acceptCookies"))
        )
        cookie_btn.click()
    except TimeoutException:
        pass


def load_all_products_on_page(driver: webdriver.Chrome, url: str) -> str:
    driver.get(url)
    accept_cookies(driver)

    while True:
        try:
            more_button = WebDriverWait(driver, 2).until(
                ec.element_to_be_clickable(
                    (By.CSS_SELECTOR, ".ecom-button, .btn-primary")
                )
            )

            driver.execute_script(
                "arguments[0].scrollIntoView(true);",
                more_button
            )
            time.sleep(0.5)

            more_button.click()
            time.sleep(1)

        except (TimeoutException, ElementClickInterceptedException):
            break

    try:
        WebDriverWait(driver, 5).until(
            ec.presence_of_element_located((By.CLASS_NAME, "ws-icon-star"))
        )
    except TimeoutException:
        time.sleep(1)

    return driver.page_source


def parse_products_from_html(html_content: str) -> list[Product]:
    soup = BeautifulSoup(html_content, "html.parser")
    products = []

    product_cards = soup.find_all("div", class_="thumbnail")

    for card in product_cards:
        title = (
            el.get("title") or el.text.strip()
            if (el := card.find("a", class_="title"))
            else ""
        )
        description = (
            " ".join(el.text.split())
            if (el := card.find("p", class_="description"))
            else ""
        )

        price = (
            float(el.text.strip().replace("$", ""))
            if (el := card.find("h4", class_="price"))
            else 0.0
        )

        num_of_reviews = (
            int(el.text.strip().split()[0])
            if (el := card.find("p", class_="review-count"))
            else 0
        )

        rating_element = card.find(lambda tag: tag.has_attr("data-rating"))

        if rating_element:
            rating = int(rating_element.get("data-rating"))
        else:
            rating = len(card.find_all("span", class_="ws-icon-star"))

        products.append(Product(
            title=title,
            description=description,
            price=price,
            rating=rating,
            num_of_reviews=num_of_reviews
        ))

    return products


def save_to_csv(filename: str, products: list[Product]) -> None:
    field_names = [f.name for f in fields(Product)]

    with open(filename, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=field_names)
        writer.writeheader()
        for prod in products:
            writer.writerow(prod.__dict__)


def get_all_products() -> None:
    driver = get_driver()

    try:
        for page_name, url in tqdm(
                PAGES_CONFIG.items(),
                desc="Scraping E-commerce site"
        ):
            html_content = load_all_products_on_page(driver, url)

            products = parse_products_from_html(html_content)

            csv_filename = f"{page_name}.csv"
            save_to_csv(csv_filename, products)

    finally:
        driver.quit()


if __name__ == "__main__":
    get_all_products()
