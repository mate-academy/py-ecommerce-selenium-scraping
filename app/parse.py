import csv
import os
from dataclasses import dataclass
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common import (
    TimeoutException,
    NoSuchElementException,
    ElementNotInteractableException,
    WebDriverException,
)
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait


BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")

COMPUTERS_URL = urljoin(HOME_URL, "computers/")
LAPTOPS_URL = urljoin(COMPUTERS_URL, "laptops")
TABLETS_URL = urljoin(COMPUTERS_URL, "tablets")

PHONES_URL = urljoin(HOME_URL, "phones/")
TOUCH_URL = urljoin(PHONES_URL, "touch")


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


def parse_single_product(product_soup: BeautifulSoup) -> Product:
    title = product_soup.select_one(".title")["title"]
    description = product_soup.select_one(".description").text
    description = description.replace("\xa0", " ").strip()
    price = product_soup.select_one(".price").text
    price = float(price.replace("$", "").strip())
    rating = len(product_soup.select("p > .ws-icon-star"))
    num_of_reviews = product_soup.select_one(".review-count").text
    num_of_reviews = int(num_of_reviews.split(" ")[0].strip())
    return Product(
        title=title,
        description=description,
        price=price,
        rating=rating,
        num_of_reviews=num_of_reviews
    )


def parse_product_page(page_soup: BeautifulSoup) -> list[Product]:
    products_soup = page_soup.select(".thumbnail")
    return [
        parse_single_product(product_soup)
        for product_soup in products_soup
    ]


def accept_cookies(driver: webdriver.Chrome) -> None:
    try:
        cookie_button = WebDriverWait(driver, 10).until(
            ec.presence_of_element_located((By.CLASS_NAME, "acceptCookies"))
        )
        cookie_button.click()
    except (
            TimeoutException,
            NoSuchElementException,
            ElementNotInteractableException
    ) as e:
        print(f"Error interacting with the cookie accept button: {e}")
    except WebDriverException as e:
        print(f"WebDriver exception occurred: {e}")


def more_button(driver: webdriver.Chrome) -> bool:
    try:
        button = WebDriverWait(driver, 10).until(
            ec.element_to_be_clickable(
                (By.CSS_SELECTOR, "a.ecomerce-items-scroll-more")
            )
        )
        button.click()
        WebDriverWait(driver, 10).until(
            ec.presence_of_element_located((By.CSS_SELECTOR, ".thumbnail"))
        )
        return True
    except TimeoutException:
        print("Timeout waiting for more button to be clickable.")
    except Exception as e:
        print(f"Error clicking more button: {e}")
    return False


def scrape_products(driver: webdriver.Chrome, url: str) -> list[Product]:
    all_products = []
    driver.get(url)

    accept_cookies(driver)

    while more_button(driver):
        pass

    page_soup = BeautifulSoup(driver.page_source, "html.parser")
    all_products.extend(parse_product_page(page_soup))

    return all_products


def save_products_to_csv(
        products: list,
        output_csv_path: str
) -> None:
    file_exists = os.path.isfile(output_csv_path)
    is_file_empty = (
        os.stat(output_csv_path).st_size == 0 if file_exists else True
    )

    with open(output_csv_path, "a", newline="") as csv_file:
        writer = csv.writer(csv_file)

        if not file_exists or is_file_empty:
            writer.writerow(
                ["title", "description", "price", "rating", "num_of_reviews"]
            )

        for product in products:
            writer.writerow(
                [product.title, product.description, product.price,
                 product.rating, product.num_of_reviews]
            )


def get_all_products() -> None:
    options = Options()
    options.headless = True
    service = Service()

    driver = webdriver.Chrome(service=service, options=options)

    try:
        products_home = scrape_products(driver, HOME_URL)
        products_computers = scrape_products(driver, COMPUTERS_URL)
        products_laptops = scrape_products(driver, LAPTOPS_URL)
        products_tablets = scrape_products(driver, TABLETS_URL)
        products_phones = scrape_products(driver, PHONES_URL)
        products_touch = scrape_products(driver, TOUCH_URL)

        save_products_to_csv(products_home, "home.csv")
        save_products_to_csv(products_computers, "computers.csv")
        save_products_to_csv(products_laptops, "laptops.csv")
        save_products_to_csv(products_tablets, "tablets.csv")
        save_products_to_csv(products_phones, "phones.csv")
        save_products_to_csv(products_touch, "touch.csv")
    finally:
        driver.quit()


if __name__ == "__main__":
    get_all_products()
