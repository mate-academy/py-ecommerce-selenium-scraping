import csv
from dataclasses import dataclass, fields
from urllib.parse import urljoin

from bs4 import BeautifulSoup, Tag
from selenium import webdriver
from selenium.common import NoSuchElementException
from selenium.webdriver.common.by import By

BASE_URL = "https://webscraper.io/"

PAGES = {
    "home": urljoin(BASE_URL, "test-sites/e-commerce/more/"),
    "computers": urljoin(BASE_URL, "test-sites/e-commerce/more/computers"),
    "laptops": urljoin(BASE_URL,
                       "test-sites/e-commerce/more/computers/laptops"),
    "tablets": urljoin(BASE_URL,
                       "test-sites/e-commerce/more/computers/tablets"),
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


def parse_single_product(product_soup: Tag) -> Product:
    return Product(
        title=product_soup.select_one(".title")["title"],
        description=product_soup.select_one(".description").text.replace(
            "\xa0", " "
        ),
        price=float(product_soup.select_one(".price")
                    .text.replace("$", "")),
        rating=len(product_soup.select("span.ws-icon-star")),
        num_of_reviews=int(
            product_soup.select_one(".review-count").text.split()[0]
        ),
    )


def parse_all_products(url: str) -> list[Product]:
    driver = webdriver.Chrome()
    driver.get(url)
    try:
        more_button = driver.find_element(By.CLASS_NAME, "btn")
    except NoSuchElementException:
        more_button = None
    if more_button:
        while not more_button.get_property("style"):
            driver.execute_script("arguments[0].click();", more_button)

    soup = BeautifulSoup(driver.page_source, "html.parser")

    product_cards = soup.select(".thumbnail")
    products = [parse_single_product(product) for product in product_cards]

    return products


def save_to_csv(products: list[Product], file_name: str) -> None:

    with open(file_name, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=PRODUCT_FIELDS)
        writer.writeheader()
        for product in products:
            row = {
                "title": product.title,
                "description": product.description,
                "price": product.price,
                "rating": product.rating,
                "num_of_reviews": product.num_of_reviews,
            }
            writer.writerow(row)


def get_all_products() -> None:

    for page_name, page_url in PAGES.items():
        products = parse_all_products(page_url)
        save_to_csv(products, f"{page_name}.csv")


if __name__ == "__main__":
    get_all_products()
