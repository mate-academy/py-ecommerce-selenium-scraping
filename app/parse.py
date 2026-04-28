import csv
import time
from dataclasses import dataclass, fields, astuple
from urllib.parse import urljoin
from bs4 import BeautifulSoup, Tag
from selenium import webdriver
from selenium.common import NoSuchElementException

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


BASE_URL = "https://webscraper.io/"

URLS = {
    "home": urljoin(BASE_URL, "test-sites/e-commerce/more/"),
    "computers": urljoin(BASE_URL, "test-sites/e-commerce/more/computers"),
    "laptops": urljoin(BASE_URL, "test-sites/e-commerce/more/computers/laptops"),
    "tablets": urljoin(BASE_URL, "test-sites/e-commerce/more/computers/tablets"),
    "phones": urljoin(BASE_URL, "test-sites/e-commerce/more/phones"),
    "touch": urljoin(BASE_URL, "test-sites/e-commerce/more/phones/touch"),
}


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


PRODUCT_FIELDS = [field.name for field in fields(Product)]


def safe_int(value, default=0):
    try:
        return int(value)
    except:
        return default


def accept_cookies(driver):
    try:
        button = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Accept')]"))
        )
        button.click()
    except:
        pass


def parse_one_product(product: Tag) -> Product:
    rating_tag = product.select_one("p[data-rating]")
    return Product(
        title=product.select_one(".title")["title"],
        description=product.select_one(".description").text,
        price=float(product.select_one(".price").text.replace("$", "")),
        rating = safe_int(rating_tag["data-rating"] if rating_tag else None),
        num_of_reviews=int(product.select_one(".review-count").text.split()[0])
    )


def get_products_per_page(soup: BeautifulSoup) -> list[Product]:
    products = soup.select(".card-body")
    return [parse_one_product(product) for product in products]


def click_all_more(driver):
    last_count = 0
    stuck_counter = 0

    while True:
        items = driver.find_elements(By.CSS_SELECTOR, ".card")
        current_count = len(items)

        if current_count == last_count:
            stuck_counter += 1
        else:
            stuck_counter = 0

        if stuck_counter >= 2:
            break

        last_count = current_count

        try:
            button = driver.find_element(By.CSS_SELECTOR, ".ecomerce-items-scroll-more")

            driver.execute_script("arguments[0].scrollIntoView(true);", button)
            time.sleep(0.5)

            driver.execute_script("arguments[0].click();", button)
            time.sleep(1)

        except NoSuchElementException:
            break
        except Exception:
            break

def get_products(url: str, new_driver) -> list[Product]:
    driver.get(url)

    accept_cookies(driver)

    click_all_more(driver)

    html = driver.page_source
    soup = BeautifulSoup(html, "html.parser")

    return get_products_per_page(soup)


def get_all_products(driver) -> None:
    for name, url in URLS.items():
        print(f"Parsing {name}...")
        products = get_products(url, driver)
        write_to_csv(products, name)


def write_to_csv(products: list[Product], name: str):
    with open(f"{name}.csv", "w") as f:
        writer = csv.writer(f)
        writer.writerow(PRODUCT_FIELDS)
        writer.writerows([astuple(product) for product in products])


if __name__ == "__main__":
    with webdriver.Chrome() as driver:
        get_all_products(driver)
