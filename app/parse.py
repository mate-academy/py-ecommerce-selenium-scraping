import csv
from dataclasses import astuple, dataclass, fields
from urllib.parse import urljoin

from selenium import webdriver
from selenium.common.exceptions import (
    NoSuchElementException,
    TimeoutException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait
from tqdm import tqdm


BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")

PAGES = {
    "home": HOME_URL,
    "computers": urljoin(HOME_URL, "computers"),
    "laptops": urljoin(HOME_URL, "computers/laptops"),
    "tablets": urljoin(HOME_URL, "computers/tablets"),
    "phones": urljoin(HOME_URL, "phones"),
    "touch": urljoin(HOME_URL, "phones/touch"),
}

PRODUCT_SELECTOR = ".thumbnail"
MORE_BUTTON_SELECTOR = ".ecomerce-items-scroll-more"
COOKIE_BUTTON_SELECTOR = ".acceptCookies"
WAIT_TIMEOUT = 10


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


PRODUCT_FIELDS = [field.name for field in fields(Product)]


def parse_single_product(product_card: WebElement) -> Product:
    return Product(
        title=product_card.find_element(
            By.CSS_SELECTOR, ".title"
        ).get_attribute("title"),
        description=product_card.find_element(
            By.CSS_SELECTOR, ".description"
        ).text,
        price=float(
            product_card.find_element(
                By.CSS_SELECTOR, ".price"
            ).text.replace("$", "")
        ),
        rating=len(
            product_card.find_elements(By.CSS_SELECTOR, ".ws-icon-star")
        ),
        num_of_reviews=int(
            product_card.find_element(
                By.CSS_SELECTOR, ".review-count"
            ).text.split()[0]
        ),
    )


def accept_cookies(driver: WebDriver) -> None:
    try:
        driver.find_element(By.CSS_SELECTOR, COOKIE_BUTTON_SELECTOR).click()
    except NoSuchElementException:
        pass


def load_all_products(driver: WebDriver) -> None:
    """Click the "More" button until it disappears."""
    wait = WebDriverWait(driver, WAIT_TIMEOUT)

    while True:
        try:
            more_button = driver.find_element(
                By.CSS_SELECTOR, MORE_BUTTON_SELECTOR
            )
        except NoSuchElementException:
            return

        if not more_button.is_displayed():
            return

        products_count = len(
            driver.find_elements(By.CSS_SELECTOR, PRODUCT_SELECTOR)
        )
        driver.execute_script("arguments[0].click();", more_button)

        try:
            wait.until(
                lambda drv: len(
                    drv.find_elements(By.CSS_SELECTOR, PRODUCT_SELECTOR)
                ) > products_count
            )
        except TimeoutException:
            return


def get_page_products(driver: WebDriver, url: str) -> list[Product]:
    driver.get(url)
    WebDriverWait(driver, WAIT_TIMEOUT).until(
        ec.presence_of_element_located((By.CSS_SELECTOR, PRODUCT_SELECTOR))
    )
    accept_cookies(driver)
    load_all_products(driver)

    return [
        parse_single_product(product_card)
        for product_card in driver.find_elements(
            By.CSS_SELECTOR, PRODUCT_SELECTOR
        )
    ]


def write_products_to_csv(products: list[Product], file_name: str) -> None:
    with open(file_name, "w", newline="", encoding="utf-8") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(PRODUCT_FIELDS)
        writer.writerows(astuple(product) for product in products)


def create_driver() -> WebDriver:
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--window-size=1920,1080")
    return webdriver.Chrome(options=options)


def get_all_products() -> None:
    driver = create_driver()
    try:
        with tqdm(PAGES.items(), desc="Scraping pages", unit="page") as bar:
            for page_name, url in bar:
                bar.set_postfix(page=page_name)
                products = get_page_products(driver, url)
                write_products_to_csv(products, f"{page_name}.csv")
    finally:
        driver.quit()


if __name__ == "__main__":
    get_all_products()
