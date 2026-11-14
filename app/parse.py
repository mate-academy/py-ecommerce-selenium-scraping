import csv
import time
from dataclasses import dataclass, fields, astuple
from urllib.parse import urljoin

from selenium import webdriver
from selenium.common.exceptions import (
    ElementClickInterceptedException,
    NoSuchElementException,
    StaleElementReferenceException,
    TimeoutException,
)
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from tqdm import tqdm

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


def get_driver(headless: bool = True) -> WebDriver:
    options = Options()
    if headless:
        options.add_argument("--headless=new")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
    return webdriver.Chrome(options=options)


def accept_cookies(driver: WebDriver, timeout: int = 3) -> None:
    try:
        accept_btn = WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable((By.CLASS_NAME, "acceptCookies"))
        )
        accept_btn.click()
    except TimeoutException:
        pass


def load_all_products(driver: WebDriver, page_name: str) -> None:
    with tqdm(
        desc=f"Expanding [{page_name}]",
        unit=" click",
        leave=False,
    ) as pbar:
        while True:
            try:
                more_btn = WebDriverWait(driver, 3).until(
                    EC.presence_of_element_located(
                        (By.CLASS_NAME, "ecomerce-items-scroll-more")
                    )
                )

                if not more_btn.is_displayed():
                    break

                driver.execute_script(
                    "arguments[0].scrollIntoView({block: 'center'});", more_btn
                )
                time.sleep(0.3)

                retries = 3
                clicked = False
                for _ in range(retries):
                    try:
                        more_btn.click()
                        clicked = True
                        break
                    except (
                        ElementClickInterceptedException,
                        StaleElementReferenceException,
                    ):
                        time.sleep(0.5)
                        try:
                            more_btn = driver.find_element(
                                By.CLASS_NAME, "ecomerce-items-scroll-more"
                            )
                            driver.execute_script(
                                "arguments[0].scrollIntoView({block: 'center'});", more_btn
                            )
                        except Exception:
                            pass

                if not clicked:
                    for _ in range(retries):
                        try:
                            more_btn = driver.find_element(
                                By.CLASS_NAME, "ecomerce-items-scroll-more"
                            )
                            driver.execute_script("arguments[0].click();", more_btn)
                            clicked = True
                            break
                        except Exception:
                            time.sleep(0.5)

                if not clicked:
                    time.sleep(1)
                    try:
                        more_btn = driver.find_element(
                            By.CLASS_NAME, "ecomerce-items-scroll-more"
                        )
                        if not more_btn.is_displayed():
                            break
                        continue
                    except Exception:
                        break

                pbar.update(1)
                time.sleep(0.5)

            except (TimeoutException, NoSuchElementException):
                break


def parse_single_product(card: WebElement) -> Product:
    title_el = card.find_element(By.CLASS_NAME, "title")
    title = title_el.get_attribute("title") or title_el.text.strip()

    description = card.find_element(By.CLASS_NAME, "description").text.strip()

    price_text = card.find_element(By.CLASS_NAME, "price").text.strip()
    price = float(price_text.replace("$", ""))

    ratings_div = card.find_element(By.CLASS_NAME, "ratings")
    stars = ratings_div.find_elements(By.CLASS_NAME, "ws-icon-star")
    if not stars:
        stars = ratings_div.find_elements(By.CLASS_NAME, "glyphicon-star")
    rating = len(stars)

    reviews_text = ratings_div.find_element(By.CLASS_NAME, "review-count").text.strip()
    num_of_reviews = int(reviews_text.split()[0])

    return Product(
        title=title,
        description=description,
        price=price,
        rating=rating,
        num_of_reviews=num_of_reviews,
    )


def parse_single_page(driver: WebDriver, page_name: str, url: str) -> list[Product]:
    driver.get(url)
    accept_cookies(driver)
    load_all_products(driver, page_name)

    product_cards = driver.find_elements(By.CLASS_NAME, "thumbnail")
    return [
        parse_single_product(card)
        for card in tqdm(
            product_cards,
            desc=f"Parsing   [{page_name}]",
            unit=" item",
            leave=False,
        )
    ]


def write_products_to_csv(products: list[Product], filename: str) -> None:
    header = [field.name for field in fields(Product)]
    with open(filename, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(header)
        for product in products:
            writer.writerow(astuple(product))


def get_all_products() -> None:
    driver = get_driver(headless=True)
    try:
        for page_name, relative_path in tqdm(
            PAGES.items(), desc="Overall Progress", unit=" page"
        ):
            full_url = urljoin(HOME_URL, relative_path)
            products = parse_single_page(driver, page_name, full_url)
            write_products_to_csv(products, f"{page_name}.csv")
    finally:
        driver.quit()


if __name__ == "__main__":
    get_all_products()
