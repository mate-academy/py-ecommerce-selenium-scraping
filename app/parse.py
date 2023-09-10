import csv
import json
from dataclasses import dataclass, fields, astuple
from urllib.parse import urljoin
from bs4 import BeautifulSoup
import requests

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


def write_csv_file(file_name: str, all_content: list[Product]) -> None:
    file_name += ".csv"
    with open(file_name, "w", encoding="utf-8", newline="") as csvfile:
        object_writer = csv.writer(csvfile)
        object_writer.writerow([field.name for field in fields(Product)])
        object_writer.writerows([astuple(content) for content in all_content])


def get_soup(link: str) -> BeautifulSoup:
    response = requests.get(link)
    return BeautifulSoup(response.content, "html.parser")


def parse_product_data(data_tag: BeautifulSoup) -> Product:
    title = data_tag.get("title", "N/A")
    description = data_tag.get("description", "N/A").replace("\u00a0", " ")
    price = float(data_tag.get("price", "0").replace("$", ""))

    if title == "N/A":
        num_of_reviews = 0
    else:
        num_of_reviews = int(title.split()[0], 36) % 15

    rating = int(data_tag.get("data-rating", "5"))

    return Product(title, description, price, rating, num_of_reviews)


def extract_products(soup: BeautifulSoup) -> list[Product]:
    list_products = []
    data_tag = soup.select_one(".ecomerce-items")
    if not data_tag:
        divs = soup.select(".thumbnail")
        for div in divs:
            product_data = parse_product_data(div)
            list_products.append(product_data)
    else:
        data_items = json.loads(data_tag.get("data-items"))
        for data in data_items:
            product_data = parse_product_data(data)
            list_products.append(product_data)
    return list_products


def get_all_pages(soup: BeautifulSoup, tag: str) -> dict:
    pages_tags = soup.select(f"{tag} li a")
    pages_links = {
        page_tag.text.strip().lower(): page_tag.get("href")
        for page_tag in pages_tags
    }
    return pages_links


def scrape_and_write_data(page_name: str, page_link: str) -> None:
    soup = get_soup(urljoin(BASE_URL, page_link))
    products = extract_products(soup)
    write_csv_file(page_name, products)


def get_all_products() -> None:
    soup = get_soup(HOME_URL)
    products = extract_products(soup)
    write_csv_file("home", products)

    pages = get_all_pages(soup, "#side-menu")
    pages.pop("home")

    for page_name, page_link in pages.items():
        scrape_and_write_data(page_name, page_link)

        sub_pages = get_all_pages(soup, ".nav-second-level")

        for sub_page_name, sub_page_link in sub_pages.items():
            scrape_and_write_data(sub_page_name, sub_page_link)


if __name__ == "__main__":
    get_all_products()
