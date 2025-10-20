import csv
import time
from dataclasses import dataclass, fields, astuple
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup, Tag

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")
COMPUTERS_URL = urljoin(HOME_URL, "computers/")
LAPTOPS_URL = urljoin(COMPUTERS_URL, "laptops")
TABLETS_URL = urljoin(COMPUTERS_URL, "tablets")
PHONES_URL = urljoin(HOME_URL, "phones/")
TOUCH_URL = urljoin(PHONES_URL, "touch")
print(TOUCH_URL)
PAGES = {
    "home": HOME_URL,
    "computers": COMPUTERS_URL,
    "laptops": LAPTOPS_URL,
    "tablets": TABLETS_URL,
    "phones": PHONES_URL,
    "touch": TOUCH_URL,
}


DYNAMIC_PAGES = ["laptops", "tablets", "touch"]


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


PRODUCT_FIELDS = [field.name for field in fields(Product)]


def create_driver() -> webdriver.Chrome:
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    driver = webdriver.Chrome(options=options)
    return driver


def parse_single_product(product: Tag) -> Product:
    return Product(
        title=product.select_one(".title")["title"],
        description=product.select_one(".description").text.strip(),
        price=float(product.select_one(".price")
                    .text.strip().replace("$", "")),
        rating=len(product.select(".ratings .ws-icon-star")),
        num_of_reviews=int(
            product.select_one(
                ".ratings .review-count span[itemprop='reviewCount']"
            ).text.strip()
        ),
    )


def get_single_page_products(page_soup: Tag) -> list[Product]:
    products = page_soup.select(".thumbnail")
    return [parse_single_product(p) for p in products]


def scrape_static_page(url: str) -> list[Product]:
    resp = requests.get(url)
    soup = BeautifulSoup(resp.text, "html.parser")
    return get_single_page_products(soup)


def scrape_dynamic_page(url: str) -> list[Product]:
    driver = create_driver()
    with driver:
        driver.get(url)
        time.sleep(1)
        while True:
            more_btn = driver.find_element(
                By.CSS_SELECTOR, "a.ecomerce-items-scroll-more"
            )
            if not more_btn.is_displayed():
                break

            more_btn.click()
            time.sleep(1)

        soup = BeautifulSoup(driver.page_source, "html.parser")
        products = get_single_page_products(soup)

        return products


def write_products_to_csv(products: [Product], output_csv_path: str) -> None:
    with open(output_csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(PRODUCT_FIELDS)
        writer.writerows([astuple(p) for p in products])


def get_all_products() -> list[Product]:
    for page_name, page_url in PAGES.items():
        print(f"\n[{page_name.upper()}]")

        if page_name in DYNAMIC_PAGES:
            products = scrape_dynamic_page(page_url)
        else:
            products = scrape_static_page(page_url)

        output_path = f"{page_name}.csv"
        write_products_to_csv(products, output_path)
        print(f"✓ Saved to {output_path}")


if __name__ == "__main__":
    get_all_products()
