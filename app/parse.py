import csv
import logging
from dataclasses import dataclass, fields
from urllib.parse import urljoin

from selenium import webdriver
from selenium.common.exceptions import (
    ElementClickInterceptedException,
    NoSuchElementException,
    StaleElementReferenceException,
    TimeoutException,
)
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC  # noqa
from selenium.webdriver.support.ui import WebDriverWait
from tqdm import tqdm
from webdriver_manager.chrome import ChromeDriverManager

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

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


def get_driver() -> WebDriver:
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--ignore-certificate-errors")
    chrome_options.add_argument("--window-size=1920,1080")

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
            current_cards = driver.find_elements(By.CLASS_NAME, "thumbnail")
            current_count = len(current_cards)

            try:
                more_btn = driver.find_element(By.CLASS_NAME,
                                               "ecomerce-items-scroll-more")
                if not more_btn.is_displayed():
                    break
            except NoSuchElementException:
                break

            try:
                driver.execute_script("arguments[0].scrollIntoView();",
                                      more_btn)
                WebDriverWait(driver, 2).until(
                    EC.element_to_be_clickable(
                        (By.CLASS_NAME, "ecomerce-items-scroll-more"))
                )
                more_btn.click()
            except (ElementClickInterceptedException,
                    StaleElementReferenceException):
                driver.execute_script("arguments[0].click();", more_btn)

            try:
                WebDriverWait(driver, 10).until(
                    lambda d: len(d.find_elements(By.CLASS_NAME,
                                                  "thumbnail")) > current_count
                )
            except TimeoutException:
                break

        except Exception:
            break


def parse_product_card(card_element: WebElement) -> Product | None:
    try:
        title = card_element.find_element(By.CLASS_NAME,
                                          "title").get_attribute("title")
        if not title:
            title = card_element.find_element(By.CLASS_NAME, "title").text

        description = card_element.find_element(By.CLASS_NAME,
                                                "description").text

        price_text = card_element.find_element(By.CLASS_NAME, "price").text
        clean_price = "".join(c for c in price_text if c.isdigit() or c == ".")
        price = float(clean_price) if clean_price else 0.0

        num_of_reviews = 0
        try:
            ratings_container = card_element.find_element(By.CLASS_NAME,
                                                          "ratings")
            paragraphs = ratings_container.find_elements(By.TAG_NAME, "p")
            for paragraph in paragraphs:
                if "reviews" in paragraph.text:
                    num_of_reviews = int(paragraph.text.split()[0])
                    break
        except Exception:
            pass

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
    except Exception:
        return None


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

            try:
                WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located(
                        (By.CLASS_NAME, "thumbnail"))
                )
            except TimeoutException:
                continue

            load_all_products(driver)

            product_cards = driver.find_elements(By.CLASS_NAME, "thumbnail")
            products_list = []

            for card in product_cards:
                product_obj = parse_product_card(card)
                if product_obj:
                    products_list.append(product_obj)

            save_to_csv(name, products_list)
    finally:
        driver.quit()


if __name__ == "__main__":
    get_all_products()
