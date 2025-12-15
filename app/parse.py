import csv
from dataclasses import dataclass, fields, astuple
import time

from bs4 import BeautifulSoup, Tag
from urllib.parse import urljoin
from selenium import webdriver
from selenium.common import NoSuchElementException
from selenium.common import ElementNotInteractableException
from selenium.webdriver.common.by import By


BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")
COMPUTER_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/computers")
LAPTOPS_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/computers/laptops")
TABLETS_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/computers/tablets")
PHONES_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/phones")
TOUCH_PHONE_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/phones/touch")

PAGE_URLS = {
    "home.csv": HOME_URL,
    "computers.csv": COMPUTER_URL,
    "laptops.csv": LAPTOPS_URL,
    "tablets.csv": TABLETS_URL,
    "phones.csv": PHONES_URL,
    "touch.csv": TOUCH_PHONE_URL,
}


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


PRODUCT_FIELDS = [field.name for field in fields(Product)]


def parser_single_product(product: Tag) -> Product:
    return Product(
        title=product.select_one(".title")["title"],
        description=product.select_one(".description")
        .get_text(strip=True).replace("\xa0", " ").replace("\u00A0", " "),
        price=float(product.select_one(".price")
                    .get_text(strip=True).replace("$", "")),
        rating=len(product.find_all("span", class_="ws-icon-star")),
        num_of_reviews=int(product.select_one(".review-count")
                           .text.replace("reviews", "")),
    )


def get_all_products() -> None:
    driver = webdriver.Chrome()
    for filename, url in PAGE_URLS.items():
        driver.get(url)

        try:
            button = driver.find_element(By.CLASS_NAME, "acceptCookies")
            button.click()
        except NoSuchElementException:
            pass

        while True:
            try:
                button = driver.find_element(
                    By.CLASS_NAME, "ecomerce-items-scroll-more"
                )
                button.click()
                time.sleep(1)
            except (NoSuchElementException, ElementNotInteractableException):
                break

        soup = BeautifulSoup(driver.page_source, "html.parser")
        products = soup.select(".product-wrapper.card-body")
        product_objs = [parser_single_product(p) for p in products]

        with open(filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(PRODUCT_FIELDS)
            writer.writerows(astuple(p) for p in product_objs)
    driver.close()

def main() -> None:
    get_all_products()


if __name__ == "__main__":
    main()
