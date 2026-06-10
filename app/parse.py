import csv
from dataclasses import dataclass, fields, astuple
from urllib.parse import urljoin

from bs4 import Tag, BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


PRODUCT_FIELDS = [field.name for field in fields(Product)]


def parse_single_product(product: Tag) -> Product:
    return Product(
        title=product.select_one(".title")["title"],
        description=product.select_one(".description").text.replace("\xa0", " "),
        price=float(product.select_one(".price").text.replace("$", "")),
        rating=len(product.select(".ws-icon-star")),
        num_of_reviews=int(product.select_one(".review-count").text.split()[0]),
    )


def get_driver() -> WebDriver:
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    return webdriver.Chrome(options=options)


def accept_cookies(driver: WebDriver) -> None:
    try:
        WebDriverWait(driver, 2).until(
            ec.element_to_be_clickable((By.CLASS_NAME, "acceptCookies"))
        ).click()
    except Exception:
        pass


def get_full_page_products(driver: WebDriver, url: str) -> list[Product]:
    driver.get(url)
    accept_cookies(driver)

    while True:
        product_count_before = len(driver.find_elements(By.CSS_SELECTOR, ".card-body"))

        try:
            more_button = WebDriverWait(driver, 5).until(
                ec.element_to_be_clickable((By.CLASS_NAME, "ecomerce-items-scroll-more"))
            )

            driver.execute_script("arguments[0].click();", more_button)

            WebDriverWait(driver, 5).until(
                lambda d: len(d.find_elements(By.CSS_SELECTOR, ".card-body"))
                > product_count_before
            )

        except Exception:
            break

    html = driver.page_source
    soup = BeautifulSoup(html, "html.parser")
    product_tags = soup.select(".card-body")

    return [parse_single_product(tag) for tag in product_tags]


def write_products_to_csv(path: str, products: list[Product]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(PRODUCT_FIELDS)
        writer.writerows([astuple(product) for product in products])


def get_all_products() -> None:
    pages = [
        (HOME_URL, "home.csv"),
        (urljoin(HOME_URL, "computers"), "computers.csv"),
        (urljoin(HOME_URL, "computers/laptops"), "laptops.csv"),
        (urljoin(HOME_URL, "computers/tablets"), "tablets.csv"),
        (urljoin(HOME_URL, "phones"), "phones.csv"),
        (urljoin(HOME_URL, "phones/touch"), "touch.csv"),
    ]
    with get_driver() as driver:
        for url, filename in pages:
            products = get_full_page_products(driver, url)
            write_products_to_csv(filename, products)


if __name__ == "__main__":
    get_all_products()
