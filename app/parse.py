import csv
import time
from dataclasses import dataclass
from selenium.webdriver.support import expected_conditions as EC
from urllib.parse import urljoin
from selenium import webdriver
from selenium.common import NoSuchElementException, ElementNotInteractableException, TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")

URLS = {
    "home": HOME_URL,
    "computers": urljoin(BASE_URL, "test-sites/e-commerce/more/computers"),
    "laptops": urljoin(BASE_URL, "test-sites/e-commerce/more/computers/laptops"),
    "tablets": urljoin(BASE_URL, "test-sites/e-commerce/more/computers/tablets"),
    "phones": urljoin(BASE_URL, "test-sites/e-commerce/more/phones"),
    "touch": urljoin(BASE_URL, "test-sites/e-commerce/more/phones/touch"),
}


def accept_cookies(driver: WebDriver) -> None:
    locators = [
        (By.CLASS_NAME, "acceptCookies"),
        (By.ID, "cookieConsentButton"),
        (By.XPATH, "//button[contains(text(),'Accept')]")
    ]
    for by, value in locators:
        try:
            btn = WebDriverWait(driver, 5).until(EC.element_to_be_clickable((by, value)))
            btn.click()
            break
        except TimeoutException:
            continue


def init_driver() -> WebDriver:
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(options=options)
    driver.implicitly_wait(3)
    return driver


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


def parse_product(product) -> Product:
    try:
        title_part = product.find_element(By.CLASS_NAME, "title")
        title = title_part.get_attribute("title")

        description_part = product.find_element(By.CLASS_NAME, "description")
        description = description_part.text.strip()

        price_part = product.find_element(By.CLASS_NAME, "price")
        price = float(price_part.text.replace("$", "").strip())

        reviews_part = product.find_element(By.CLASS_NAME, "ratings")
        rating_icons = reviews_part.find_elements(By.CLASS_NAME, "ws-icon-star")
        rating = len(rating_icons)

        reviews_count = reviews_part.find_element(
            By.CLASS_NAME, "review-count"
        ).text.strip()
        num_of_reviews = int(reviews_count.split()[0])

        return Product(
            title=title,
            description=description,
            price=price,
            rating=rating,
            num_of_reviews=num_of_reviews,
        )
    except Exception:
        return None


def more_button(url: str, driver: WebDriver) -> None:
    driver.get(url)
    accept_cookies(driver)
    wait = WebDriverWait(driver, 10)

    prev_count = 0
    while True:
        products = driver.find_elements(By.CLASS_NAME, "thumbnail")
        current_count = len(products)

        try:
            more_btn = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "ecomerce-items-scroll-more")))
            more_btn.click()

            wait.until(lambda d: len(d.find_elements(By.CLASS_NAME, "thumbnail")) > current_count)
        except (TimeoutException, NoSuchElementException, ElementNotInteractableException):
            break

        new_count = len(driver.find_elements(By.CLASS_NAME, "thumbnail"))
        if new_count == current_count:
            break


def parse_pages(url: str, driver: WebDriver) -> list[Product]:
    more_button(url, driver)
    products = driver.find_elements(By.CLASS_NAME, "thumbnail")
    return [parse_product(p) for p in products]


def write_products_to_csv(category: str, products: list[Product | None]) -> None:
    valid_products = [p for p in products if p is not None]

    with open(f"{category}.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["title", "description", "price", "rating", "num_of_reviews"])
        for product in valid_products:
            writer.writerow([
                product.title,
                product.description,
                product.price,
                product.rating,
                product.num_of_reviews,
            ])


def get_all_products() -> None:
    driver = init_driver()
    try:
        for category, url in URLS.items():
            products = parse_pages(url, driver)
            write_products_to_csv(category, products)
    finally:
        driver.quit()



if __name__ == "__main__":
    get_all_products()
