import csv
import time
from dataclasses import dataclass, fields
from urllib.parse import urljoin

from selenium import webdriver
from selenium.common.exceptions import (
    ElementClickInterceptedException,
    NoSuchElementException,
    TimeoutException,
)
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC # noqa
from selenium.webdriver.support.ui import WebDriverWait
from tqdm import tqdm
from webdriver_manager.chrome import ChromeDriverManager

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")

PAGES = {
    "home": "",
    "computers": "computers",
    "laptops": "computers/laptops",
    "tablets": "computers/tablets",
    "phones": "phones",
    "touch": "phones/touch",
}


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


PRODUCT_FIELDS = [field.name for field in fields(Product)]


def get_driver() -> webdriver.Chrome:
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--ignore-certificate-errors")

    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=chrome_options)


def accept_cookies(driver: WebDriver) -> None:
    try:
        cookie_btn = WebDriverWait(driver, 3).until(
            EC.element_to_be_clickable((By.CLASS_NAME, "acceptCookies"))
        )
        cookie_btn.click()
    except TimeoutException:
        pass


def load_all_products(driver: WebDriver) -> None:
    while True:
        try:
            more_btn = driver.find_element(By.CLASS_NAME,
                                           "ecomerce-items-scroll-more")
            if not more_btn.is_displayed():
                break

            driver.execute_script("arguments[0].scrollIntoView();", more_btn)
            more_btn.click()

            time.sleep(0.5)
        except (NoSuchElementException, ElementClickInterceptedException):
            break
        except Exception:
            break


def parse_product_card(card_element: WebElement) -> Product:
    title = card_element.find_element(By.CLASS_NAME, "title").get_attribute(
        "title")
    description = card_element.find_element(By.CLASS_NAME, "description").text

    price_text = card_element.find_element(By.CLASS_NAME, "price").text
    price = float(price_text.replace("$", "").replace(",", ""))

    reviews_element = card_element.find_element(By.CSS_SELECTOR,
                                                ".ratings .pull-right")
    reviews_text = reviews_element.text
    if reviews_text:
        num_of_reviews = int(reviews_text.split()[0])
    else:
        num_of_reviews = 0

    rating_stars = card_element.find_elements(By.CSS_SELECTOR,
                                              ".ratings .glyphicon-star")
    rating = len(rating_stars)

    return Product(
        title=title,
        description=description,
        price=price,
        rating=rating,
        num_of_reviews=num_of_reviews
    )


def save_to_csv(filename: str, products: list[Product]) -> None:
    with open(f"{filename}.csv", "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(PRODUCT_FIELDS)
        for product in products:
            writer.writerow([
                product.title,
                product.description,
                product.price,
                product.rating,
                product.num_of_reviews
            ])


def get_all_products() -> None:
    driver = get_driver()
    try:
        for name, url_suffix in tqdm(PAGES.items()):
            full_url = urljoin(HOME_URL, url_suffix)
            driver.get(full_url)
            accept_cookies(driver)
            load_all_products(driver)
            product_cards = driver.find_elements(By.CLASS_NAME, "thumbnail")
            products_list = []
            for card in product_cards:
                products_list.append(parse_product_card(card))

            save_to_csv(name, products_list)
    finally:
        driver.quit()


if __name__ == "__main__":
    get_all_products()
