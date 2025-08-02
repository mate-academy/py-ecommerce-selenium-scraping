import csv
import json
import logging
import sys
from dataclasses import dataclass, fields, asdict
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup, Tag
from selenium import webdriver
from selenium.webdriver.common.by import By

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("parser.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")

driver = webdriver.Chrome()


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


def save_data_to_csv(name: str, products: list[Product]) -> None:
    with open(f"{name}.csv", mode="w", newline="", encoding="utf-8") as csvfile:
        fieldnames = [field.name for field in fields(Product)]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        if products is None:
            return
        for product in products:
            writer.writerow(asdict(product))  # Serialize and write


def make_safe_request(url: str) -> str:
    try:
        response = requests.get(url=url)
        if response.status_code == 200:
            return response.text
    except Exception as e:
        logging.warning(e)


def get_soup_from_page(url: str) -> BeautifulSoup | None:
    soup = BeautifulSoup(make_safe_request(url), "html.parser")
    if soup.body and "No products found!" in soup.get_text():
        return None
    return soup


def get_product_price(product: Tag) -> float:
    price_container = product.select_one(".price")
    if not price_container:
        return 0.0

    # Try nested [itemprop='price'] first
    price_tag = price_container.select_one("[itemprop='price']")
    if price_tag:
        price_text = price_tag.text.strip()
    else:
        price_text = price_container.text.strip()

    price_text = price_text.replace("$", "")

    try:
        return float(price_text)
    except ValueError:
        return 0.0


def get_product_ratings(product: Tag) -> dict:
    ratings_container = product.select_one(".ratings")

    star_count = 0
    rating_tag = ratings_container.select_one("p[data-rating]")
    if rating_tag is None:
        try:
            stars = product.select(".ws-icon.ws-icon-star")
            star_count = len(stars)
        except Exception as e:
            logging.info(f"Cannot calculate stars on card!: {e}")
    else:
        star_count = rating_tag["data-rating"]

    num_of_reviews = ratings_container.select_one("[itemprop='reviewCount']").text.strip()

    return {"rating": int(star_count), "num_of_reviews": int(num_of_reviews)}


def get_product_title(product):
    title_container = product.select_one(".title")
    return title_container["title"]


def create_product_obj(card: Tag) -> Product:
    ratings = get_product_ratings(product=card)
    return Product(
        title=get_product_title(product=card),
        description=card.select_one(".description ").text,
        price=get_product_price(product=card),
        rating=ratings["rating"],
        num_of_reviews=ratings["num_of_reviews"]
    )


def get_html_via_selenium(url: str) -> BeautifulSoup:
    driver.get(url)
    try:
        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')
        return soup
    except Exception as e:
        logging.info(f"Element not found:{e}")
    finally:
        driver.quit()


def is_btn_more(url) -> bool:
    driver.get(url)

    try:
        element = driver.find_element(By.CSS_SELECTOR, ".some-class")

        if element.is_displayed():
            print("Element is visible")
        else:
            print("Element is hidden")
    except Exception as e:
        print("Element not found:", e)


def get_products_from_single_page(soup: BeautifulSoup, url: str) -> list[Product] | None:
    products = []
    # Check button more than load all cards
    if is_btn_more(url=url) or not soup.select_one(".card-body"):
        logging.info("this page with more button")
        soup = get_html_via_selenium(url=url)

    cards = soup.select(".card-body")
    if cards:
        for card in cards:
            products.append(create_product_obj(card=card))
    else:
        logging.info("Cards not found!")
    return products

def get_products_from_page(home_url: str, path: str = None):
    url = urljoin(home_url, path)
    logging.info(f"Working on {url}")

    soup = get_soup_from_page(url=url)

    products = get_products_from_single_page(soup=soup, url=url)

    name_of_csv_file = "home"
    if path:
        name_of_csv_file = path.split("/")[-1]
    save_data_to_csv(name=name_of_csv_file, products=products)


def get_all_products() -> None:
    get_products_from_page(home_url=HOME_URL)  # home page (3 random products);
    get_products_from_page(home_url=HOME_URL, path="computers")  # computers page (3 random computers)
    get_products_from_page(home_url=HOME_URL, path="phones")  # phones page (3 random phones);
    get_products_from_page(home_url=HOME_URL, path="computers/laptops")  # laptops page (117 laptops) with more button pagination


if __name__ == "__main__":
    get_all_products()
