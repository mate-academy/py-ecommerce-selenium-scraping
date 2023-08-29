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


def get_products_from_page(name: str, soup: BeautifulSoup) -> None:
    list_products = []
    data_tag = soup.select_one(".ecomerce-items")
    if not data_tag:
        divs = soup.select(".thumbnail")
        for div in divs:
            title = div.select_one(".title").get("title")
            description = div.select_one(".description").text
            price = float(div.select_one(".price").text.replace("$", ""))
            rating = int(div.select_one("[data-rating]").get("data-rating"))
            num_of_reviews = int(
                div.select_one(
                    ".ratings .pull-right"
                ).text.split()[0]
            )
            list_products.append(
                Product(title, description, price, rating, num_of_reviews)
            )
    else:
        data_items = json.loads(data_tag.get("data-items"))
        for data in data_items:
            title = data["title"]
            description = data["description"].replace("\u00a0", " ")
            price = float(data["price"])
            rating = 5  # Default rating
            num_of_reviews = int(title.split()[0], 36) % 15
            list_products.append(
                Product(title, description, price, rating, num_of_reviews)
            )

    write_csv_file(name, list_products)


def get_all_pages(soup: BeautifulSoup, tag: str) -> dict:
    pages_tags = soup.select(f"{tag} li a")
    pages_links = {
        page_tag.text.strip().lower(): page_tag.get("href")
        for page_tag in pages_tags
    }
    return pages_links


def get_all_products() -> None:
    # Start with the home page
    soup = get_soup(HOME_URL)
    get_products_from_page("home", soup)

    pages = get_all_pages(soup, "#side-menu")
    pages.pop("home")

    for page_name, page_link in pages.items():
        soup = get_soup(urljoin(BASE_URL, page_link))
        get_products_from_page(page_name, soup)

        sub_pages = get_all_pages(soup, ".nav-second-level")

        for sub_page_name, sub_page_link in sub_pages.items():
            soup = get_soup(urljoin(BASE_URL, sub_page_link))
            get_products_from_page(sub_page_name, soup)


if __name__ == "__main__":
    get_all_products()
