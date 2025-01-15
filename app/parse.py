import csv
import time
from selenium import webdriver
from dataclasses import dataclass, fields, astuple
from urllib.parse import urljoin
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By


BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")
PAGES = {
    "home": HOME_URL,
    "computers": f"{HOME_URL}computers",
    "laptops": f"{HOME_URL}computers/laptops",
    "tablets": f"{HOME_URL}computers/tablets",
    "phones": f"{HOME_URL}phones",
    "touch": f"{HOME_URL}phones/touch",
}


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


op = webdriver.ChromeOptions()
op.add_argument("headless")
driver = webdriver.Chrome(options=op)

FIELDS = [field.name for field in fields(Product)]


def extract_product(product_element) -> Product:
    return Product(
        title=str(
            product_element.find_element(By.CSS_SELECTOR, "a.title")
            .get_attribute("title")
        ),
        description=str(
            product_element.find_element(By.CSS_SELECTOR, "p.description")
            .text
        ),
        price=float(
            product_element.find_element(By.CSS_SELECTOR, "h4.price")
            .text[1:]),
        rating=len(
            product_element.find_elements(By.CSS_SELECTOR, "span.ws-icon-star")
        ),
        num_of_reviews=int(
            product_element.find_element(By.CSS_SELECTOR, "p.review-count")
            .text.split()[0]
        ),
    )


def parse_page(url: str) -> list[Product]:
    driver.get(url)
    max_attempts = 100
    attempts = 0
    try:
        while attempts < max_attempts:
            button = driver.find_element(By.CSS_SELECTOR, ".ecomerce-items-scroll-more")
            if "display: none" in button.get_attribute("style"):
                break
            driver.execute_script("arguments[0].click();", button)
            time.sleep(0.1)
            attempts += 1
    except NoSuchElementException:
        pass
    products = []
    for product_element in driver.find_elements(By.CSS_SELECTOR, "div.card-body"):
        products.append(extract_product(product_element))
    return products


def write_to_csv(products: list[Product], file_name: str) -> None:
    with open(f"{file_name}.csv", "w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(FIELDS)
        writer.writerows(astuple(product) for product in products)


def get_all_products() -> None:
    for file_name, url in PAGES.items():
        products = parse_page(url)
        write_to_csv(products, file_name)
    driver.close()


if __name__ == "__main__":
    get_all_products()
