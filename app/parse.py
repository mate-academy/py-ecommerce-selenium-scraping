import csv
import time
from dataclasses import dataclass, astuple

from selenium.common import TimeoutException
from selenium.webdriver.support import expected_conditions as EC
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup, Tag
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from tqdm import tqdm
from webdriver_manager.chrome import ChromeDriverManager

chrome_options = Options()
chrome_options.add_argument("--headless")
service = Service(ChromeDriverManager().install())

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")
COMPUTERS_URL = urljoin(HOME_URL, "computers/")
PHONES_URL = urljoin(HOME_URL, "phones/")
LAPTOPS_URL = urljoin(COMPUTERS_URL, "laptops")
TABLETS_URL = urljoin(COMPUTERS_URL, "tablets")
TOUCH_URL = urljoin(PHONES_URL, "touch")

FIELDS = ["title", "description", "price", "rating", "num_of_reviews"]


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


def parse_single_product(product_soup: Tag) -> Product:
    return Product(
        title=product_soup.select_one(".title")["title"],
        description=product_soup.select_one(".description").text,
        price=float(product_soup.select_one(".price").text.replace("$", "")),
        rating=int(product_soup.select_one("p[data-rating]")["data-rating"]),
        num_of_reviews=int(
            product_soup.select_one("p.review-count").text.split()[0]
        ),
    )


def save_to_csv(products: list[Product], file_name: str) -> None:
    with open(file_name, "w", newline='') as f:
        writer = csv.writer(f)
        writer.writerow(FIELDS)
        writer.writerows([astuple(product) for product in tqdm(products)])


def parse_single_product_from_detail_page(url: str) -> Product:
    tablet_url = urljoin(BASE_URL, url)
    tablet_page = requests.get(tablet_url).content
    tablet_soup = BeautifulSoup(tablet_page, "html.parser")

    return Product(
        title=tablet_soup.select_one(".title").text,
        description=tablet_soup.select_one(".description").text,
        price=float(tablet_soup.select_one(".price").text.replace("$", "")),
        rating=len(tablet_soup.select("p.review-count span")),
        num_of_reviews=int(
            tablet_soup.select_one("p.review-count").text.split()[0]
        ),
    )


def get_all_products_from_their_detail_page(main_url: str) -> list[Product]:
    with webdriver.Chrome(service=service, options=chrome_options) as driver:
        driver.get(main_url)

        previous_product_count = 0
        while True:
            try:
                soup = BeautifulSoup(driver.page_source, "html.parser")
                products_on_page = len(soup.select(".thumbnail"))

                if products_on_page == previous_product_count:
                    print("Downloaded all products")
                    break

                previous_product_count = products_on_page

                more_button = WebDriverWait(driver, 2).until(
                    EC.element_to_be_clickable((By.CLASS_NAME, "ecomerce-items-scroll-more"))
                )
                more_button.click()
                time.sleep(1)

            except TimeoutException:
                print("The 'More' button was not found or is not clickable.")
                break

            except Exception as e:
                print(f"Exception: {e}")
                break

        soup = BeautifulSoup(driver.page_source, "html.parser")
        links = soup.select("a.title")
        urls = [link["href"] for link in links]

    return [parse_single_product_from_detail_page(url) for url in tqdm(urls)]


def fetch_products_from_page(url: str) -> list[Product]:
    page = requests.get(url).content
    soup = BeautifulSoup(page, "html.parser")
    products_soup = soup.select(".thumbnail")
    return [parse_single_product(product_soup) for product_soup in tqdm(products_soup)]


def get_all_products() -> None:
    home_products = fetch_products_from_page(HOME_URL)
    save_to_csv(home_products, "home.csv")

    computers_products = fetch_products_from_page(COMPUTERS_URL)
    save_to_csv(computers_products, "computers.csv")

    phones_products = fetch_products_from_page(PHONES_URL)
    save_to_csv(phones_products, "phones.csv")

    tablets = get_all_products_from_their_detail_page(TABLETS_URL)
    save_to_csv(tablets, "tablets.csv")

    laptops = get_all_products_from_their_detail_page(LAPTOPS_URL)
    save_to_csv(laptops, "laptops.csv")

    touches = get_all_products_from_their_detail_page(TOUCH_URL)
    save_to_csv(touches, "touch.csv")


if __name__ == "__main__":
    get_all_products()
