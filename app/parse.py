import csv
import time
from dataclasses import astuple, dataclass, fields
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup, Tag
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.ui import WebDriverWait

BASE_URL = "https://webscraper.io/"
LIST_URL = [
    urljoin(BASE_URL, "test-sites/e-commerce/more/"),
    urljoin(BASE_URL, "test-sites/e-commerce/more/computers/"),
    urljoin(BASE_URL, "test-sites/e-commerce/more/computers/laptops"),
    urljoin(BASE_URL, "test-sites/e-commerce/more/computers/tablets"),
    urljoin(BASE_URL, "test-sites/e-commerce/more/phones/"),
    urljoin(BASE_URL, "test-sites/e-commerce/more/phones/touch"),
]

list_name = ["home", "computers", "laptops", "tablets", "phones", "touch"]


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


PRODUCT_FIELDS = [field.name for field in fields(Product)]


def parse_single_product(product: Tag) -> Product:
    title = (
        product.select_one(".title")["title"]
        if product.select_one(".title") else ""
    )
    description_tag = product.select_one(".description")
    description = (
        description_tag.text.replace(
            "\xa0", " "
        ).strip() if description_tag else ""
    )

    price_tag = product.select_one(".price")
    price = float(price_tag.text.replace("$", "")) if price_tag else 0.0

    rating = len(product.select(".ws-icon.ws-icon-star"))

    reviews_tag = product.select_one('span[itemprop="reviewCount"]')
    num_of_reviews = int(reviews_tag.text.strip()) if reviews_tag else 0

    return Product(
        title=title.strip(),
        description=description,
        price=price,
        rating=rating,
        num_of_reviews=num_of_reviews,
    )


def get_home_products(url: str) -> [Product]:
    text = requests.get(url).content
    soup = BeautifulSoup(text, "html.parser")
    products = soup.select(".card-body")
    return [parse_single_product(product) for product in products]


def get_all_products(url: str | None = None) -> list[Product]:
    if url is None:
        url = LIST_URL[0]

    all_products = []
    driver = webdriver.Chrome()
    driver.get(url)

    while True:
        try:
            more_button = WebDriverWait(driver, 5).until(
                expected_conditions.element_to_be_clickable(
                    (
                        By.CSS_SELECTOR,
                        "a.ecommerce-items-scroll-more, "
                        "button.ecommerce-items-scroll-more, "
                        ".btn-primary",
                    )
                )
            )
            driver.execute_script("arguments[0].click();", more_button)
            time.sleep(2)
        except Exception:
            break

    html = driver.page_source
    driver.quit()

    soup = BeautifulSoup(html, "html.parser")
    products = soup.select(".product-wrapper.card-body")

    for prod in products:
        all_products.append(parse_single_product(prod))

    return all_products


def write_products_to_csv(products: [Product], name: str) -> None:
    with open(name, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(PRODUCT_FIELDS)
        writer.writerows([astuple(product) for product in products])


def main(output_csv_path: str, url: str | None = None) -> None:
    products = get_all_products(url)
    write_products_to_csv(products, output_csv_path)


for i, url in enumerate(LIST_URL):
    file_name = f"{list_name[i]}.csv"
    main(file_name, url)
