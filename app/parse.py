import csv
import time
from dataclasses import dataclass
from urllib.parse import urljoin

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.wait import WebDriverWait


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")


def get_webdriver() -> webdriver.Chrome:
    options = Options()
    options.add_argument("--headless=new")
    return webdriver.Chrome(options=options)


def accept_cookies(driver: webdriver.Chrome) -> None:
    try:
        accept_button = driver.find_element(By.CLASS_NAME, "acceptCookies")
        accept_button.click()
        time.sleep(0.1)
    except Exception:
        pass


def scrape_products_from_page(driver: webdriver.Chrome) -> list[Product]:
    products = []
    product_elements = driver.find_elements(By.CLASS_NAME, "thumbnail")

    for element in product_elements:
        product = Product(
            title=element.find_element(
                By.CLASS_NAME, "title"
            ).get_attribute("title"),
            description=(
                element
                .find_element(By.CLASS_NAME, "description")
                .text
            ),
            price=float(
                element
                .find_element(By.CLASS_NAME, "price")
                .text
                .replace("$", "")
            ),
            rating=len(element.find_elements(By.CLASS_NAME, "ws-icon-star")),
            num_of_reviews=int(
                element.find_element(By.CLASS_NAME, "ratings").text.split()[0]
            ),
        )
        products.append(product)

    return products


def load_more_items(driver: webdriver.Chrome) -> bool:
    try:
        more_button = driver.find_element(
            By.CLASS_NAME, "ecomerce-items-scroll-more"
        )
        if not more_button.is_displayed():
            return False
        wait = WebDriverWait(driver, 10)
        more_button = wait.until(ec.element_to_be_clickable(more_button))
        more_button.click()
        return True

    except Exception:
        return False


def scrape_page(driver: webdriver.Chrome, url: str) -> list[Product]:
    driver.get(url)
    accept_cookies(driver)

    while True:
        if not load_more_items(driver):
            break
    products = scrape_products_from_page(driver)

    return products


def save_products_to_csv(products: list[Product], filename: str) -> None:
    header = ["title", "description", "price", "rating", "num_of_reviews"]

    with open(filename, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(header)

        for product in products:
            row = [
                product.title,
                product.description,
                product.price,
                product.rating,
                product.num_of_reviews,
            ]
            writer.writerow(row)


def get_all_products() -> None:
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--log-level=3")
    options.add_argument("--silent")

    driver = webdriver.Chrome(options=options)

    pages_to_scrape = [
        {"url": HOME_URL, "filename": "home.csv"},
        {"url": urljoin(HOME_URL, "computers"), "filename": "computers.csv"},
        {"url": urljoin(
            HOME_URL, "computers/laptops"
        ), "filename": "laptops.csv"},
        {"url": urljoin(
            HOME_URL, "computers/tablets"
        ), "filename": "tablets.csv"},
        {"url": urljoin(HOME_URL, "phones"), "filename": "phones.csv"},
        {"url": urljoin(HOME_URL, "phones/touch"), "filename": "touch.csv"},
    ]

    for page in pages_to_scrape:
        products = scrape_page(
            driver=driver,
            url=page["url"],
        )
        save_products_to_csv(products, filename=page["filename"])

    driver.quit()


if __name__ == "__main__":
    get_all_products()
