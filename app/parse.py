import csv
from dataclasses import dataclass, fields, astuple
from urllib.parse import urljoin

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait
from tqdm import tqdm

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")

# назва csv-файлу -> адреса сторінки
PAGES = {
    "home": HOME_URL,
    "computers": urljoin(HOME_URL, "computers"),
    "laptops": urljoin(HOME_URL, "computers/laptops"),
    "tablets": urljoin(HOME_URL, "computers/tablets"),
    "phones": urljoin(HOME_URL, "phones"),
    "touch": urljoin(HOME_URL, "phones/touch"),
}

PRODUCT_SELECTOR = ".thumbnail"
MORE_BUTTON_SELECTOR = ".ecomerce-items-scroll-more"  # так, з одним "m"
COOKIES_BUTTON_SELECTOR = ".acceptCookies"
TIMEOUT = 10


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


PRODUCT_FIELDS = [field.name for field in fields(Product)]


def parse_single_product(product: WebElement) -> Product:
    return Product(
        title=product.find_element(
            By.CSS_SELECTOR, ".title"
        ).get_attribute("title"),
        description=product.find_element(
            By.CSS_SELECTOR, ".description"
        ).text,
        price=float(
            product.find_element(By.CSS_SELECTOR, ".price").text.strip("$")
        ),
        rating=len(product.find_elements(By.CSS_SELECTOR, ".ws-icon-star")),
        num_of_reviews=int(
            product.find_element(
                By.CSS_SELECTOR, ".review-count"
            ).text.split()[0]
        ),
    )


def accept_cookies(driver: WebDriver) -> None:
    try:
        WebDriverWait(driver, 3).until(
            ec.element_to_be_clickable(
                (By.CSS_SELECTOR, COOKIES_BUTTON_SELECTOR)
            )
        ).click()
    except TimeoutException:
        pass  # банера немає, нічого натискати


def count_products(driver: WebDriver) -> int:
    return len(driver.find_elements(By.CSS_SELECTOR, PRODUCT_SELECTOR))


def load_all_products(driver: WebDriver) -> None:
    while True:
        buttons = driver.find_elements(By.CSS_SELECTOR, MORE_BUTTON_SELECTOR)
        if not buttons or not buttons[0].is_displayed():
            return

        loaded = count_products(driver)
        driver.execute_script("arguments[0].click();", buttons[0])
        WebDriverWait(driver, TIMEOUT).until(
            lambda drv: count_products(drv) > loaded
        )


def scrape_page(driver: WebDriver, url: str) -> list[Product]:
    driver.get(url)
    load_all_products(driver)
    return [
        parse_single_product(product)
        for product in driver.find_elements(By.CSS_SELECTOR, PRODUCT_SELECTOR)
    ]


def write_products_to_csv(products: list[Product], path: str) -> None:
    with open(path, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(PRODUCT_FIELDS)
        writer.writerows(astuple(product) for product in products)


def get_driver() -> WebDriver:
    options = Options()
    options.add_argument("--headless=new")  # без відкриття вікна браузера
    return webdriver.Chrome(options=options)


def get_all_products() -> None:
    with get_driver() as driver:
        driver.get(HOME_URL)
        accept_cookies(driver)

        for name, url in tqdm(PAGES.items(), desc="Scraping pages"):
            products = scrape_page(driver, url)
            write_products_to_csv(products, f"{name}.csv")


if __name__ == "__main__":
    get_all_products()
