import csv
from dataclasses import dataclass, fields
import time
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common import TimeoutException, ElementClickInterceptedException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from tqdm import tqdm

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")
PAGES = {
    "home": HOME_URL,
    "computers": urljoin(HOME_URL, "computers"),
    "laptops": urljoin(HOME_URL, "computers/laptops"),
    "tablets": urljoin(HOME_URL, "computers/tablets"),
    "phones": urljoin(HOME_URL, "phones"),
    "touch": urljoin(HOME_URL, "phones/touch")
}


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


PRODUCT_FIELDS = [field.name for field in fields(Product)]


def init_driver(headless: bool = True) -> webdriver.Chrome:
    options = Options()
    options.headless = headless
    return webdriver.Chrome(options=options)


def accept_cookies(driver: webdriver.Chrome) -> None:
    try:
        cookie = WebDriverWait(driver, 3).until(
            ec.presence_of_element_located((By.CLASS_NAME, "acceptCookies"))
        )
        cookie.click()
    except (ElementClickInterceptedException, TimeoutException) as e:
        print(f"Error accepting cookies: {e}")


def click_load_more(driver: webdriver.Chrome) -> None:
    try:
        while True:
            button = WebDriverWait(driver, 1).until(
                ec.presence_of_element_located((By.CLASS_NAME, "ecomerce-items-scroll-more"))
            )
            if button.is_displayed():
                button.click()
                time.sleep(0.2)
            else:
                break
    except (TimeoutException, ElementClickInterceptedException):
        print("No more products to load or button not clickable.")


def get_product(product_soup: BeautifulSoup) -> Product:
    return Product(
        title=product_soup.select_one(".title")["title"],
        description=(product_soup.select_one(".description")
                     .text.replace("\xa0", " ").strip()),
        price=float(product_soup.select_one(".price").text.replace("$", "")),
        rating=int(len(product_soup.find_all("span", class_="ws-icon-star"))),
        num_of_reviews=int(product_soup.select_one(".review-count").text.split(" ")[0])
    )


def get_page(driver: webdriver.Chrome, page_url: str) -> list[Product]:
    try:
        driver.get(page_url)
        accept_cookies(driver)
        click_load_more(driver)
        soup = BeautifulSoup(driver.page_source, "html.parser")
        products = soup.select(".thumbnail")

        return [get_product(product) for product in products]
    except Exception as e:
        print(f"Error while getting page {page_url}: {e}")
        return []


def write_products_to_csv(output_csv_path: str, products: list[Product]) -> None:
    try:
        with open(output_csv_path, "w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(PRODUCT_FIELDS)
            for product in products:
                formatted_product = (
                    product.title,
                    product.description,
                    product.price,
                    product.rating,
                    product.num_of_reviews
                )
                writer.writerow(formatted_product)
    except IOError as e:
        print(f"Error writing to CSV {output_csv_path}: {e}")


def close_driver(driver: webdriver.Chrome) -> None:
    driver.quit()


def get_all_products() -> None:
    driver = init_driver()
    for page_name, page_url in tqdm(PAGES.items()):
        products = get_page(driver, page_url)
        if products:
            csv_filename = f"{page_name}.csv"
            write_products_to_csv(csv_filename, products)

    close_driver(driver)


if __name__ == "__main__":
    get_all_products()
