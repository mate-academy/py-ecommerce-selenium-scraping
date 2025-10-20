import csv
from dataclasses import dataclass, fields, astuple
import time
from urllib.parse import urljoin
from selenium import webdriver
from selenium.common import TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC # NOQA
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


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


PRODUCT_FIELDS = [field.name for field in fields(Product)]


def get_driver() -> WebDriver:
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(options=options)

    return driver


def accept_cookies(driver: WebDriver) -> None:
    try:
        accept_button = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable(
                (
                    By.CSS_SELECTOR,
                    "div.acceptContainer > button.acceptCookies"
                )
            )
        )
        accept_button.click()
    except TimeoutException:
        pass


def parse_single_product(product: BeautifulSoup) -> Product:
    return (Product(
        title=product.select_one(".title")["title"],
        description=product.select_one(
            ".description"
        ).text.replace("\xa0", " "),
        price=float(product.select_one(".price").text.replace("$", "")),
        rating=len(product.select(".ratings .ws-icon-star")),
        num_of_reviews=int(
            product.select_one(".review-count").text.split()[0]
        ),
    ))


def write_products_to_csv(products: [Product], filename: str) -> None:
    with open(f"{filename}.csv", "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(PRODUCT_FIELDS)
        writer.writerows([astuple(product) for product in products])


def get_products(url: str, csv_name: str) -> None:
    driver = get_driver()
    driver.get(url)
    accept_cookies(driver)
    wait = WebDriverWait(driver, 5)

    while True:
        try:
            current_count = len(driver.find_elements(By.CSS_SELECTOR, ".card-body"))
            more_button = wait.until(
                EC.element_to_be_clickable((By.CLASS_NAME, "ecomerce-items-scroll-more"))
            )
            if more_button.text.strip().lower() != "more":
                break
            more_button.click()
            wait.until(
                lambda d: len(d.find_elements(By.CSS_SELECTOR, ".card-body")) > current_count
            )

        except TimeoutException:
            break

    html = driver.page_source
    driver.quit()

    soup = BeautifulSoup(html, "html.parser")
    products = soup.select(".card-body")
    parsed_products = [parse_single_product(product) for product in products]

    write_products_to_csv(parsed_products, csv_name)


def get_all_products() -> None:
    for csv_name, url in tqdm(PAGES.items()):
        get_products(url, csv_name)


if __name__ == "__main__":
    get_all_products()
