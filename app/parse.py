import csv
from dataclasses import dataclass, astuple
from urllib.parse import urljoin

import requests as requests
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium import webdriver


BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


def get_single_product(
        title: str,
        description: str,
        price: float,
        rating: int,
        num_of_reviews: int
) -> Product:

    return Product(
        title=title,
        description=description,
        price=price,
        rating=rating,
        num_of_reviews=num_of_reviews,
    )


def get_all_products_list(soup: BeautifulSoup) -> list[Product]:
    products = []
    for product in soup:
        price = float(product.select_one(".price").text.replace("$", ""))

        title = product.select_one(".title")["title"]

        description = product.select_one(
            ".description"
        ).text.replace("\xa0", " ")

        rating = len(product.select(".ratings span"))

        num_of_reviews = int(
            product.select_one(".ratings .pull-right").text.split(" ")[0]
        )

        products.append(
            get_single_product(
                price=price,
                title=title,
                description=description,
                rating=rating,
                num_of_reviews=num_of_reviews,
            )
        )
    return products


def get_all_product_information(links: list) -> dict[list[Product]]:
    options = Options()
    options.add_argument("--headless")
    driver = webdriver.Firefox(options=options)

    products = {}

    for link in links:
        driver.get(link)

        while True:
            try:
                swatches = driver.find_element(
                    By.CLASS_NAME, "ecomerce-items-scroll-more"
                )
                swatches.click()
            except Exception:
                soup = BeautifulSoup(driver.page_source, "html.parser").select(
                    ".thumbnail"
                )
                products[link.split("/")[-1]] = get_all_products_list(soup)
                break
    return products


def get_additional_link(links: list) -> list[urljoin]:
    addition_link = []
    for link in links:
        page = requests.get(link).content
        soup = BeautifulSoup(page, "html.parser").select(".subcategory-link")
        addition_link += [urljoin(BASE_URL, link["href"]) for link in soup]

    return links + addition_link


def add_information_to_files(products: dict[list[Product]]) -> None:
    products["home"] = products["more"]

    for product in products:

        with open(product + ".csv", "w") as quotes:
            fields = (
                "title",
                "description",
                "price",
                "rating",
                "num_of_reviews"
            )

            writer = csv.writer(quotes)
            writer.writerow(fields)
            writer.writerows(astuple(prod) for prod in products[product])


def get_all_urls_for_parse() -> None:
    page = requests.get(HOME_URL).content
    soup = BeautifulSoup(page, "html.parser")
    links = [
        urljoin(BASE_URL, link["href"]) for link in soup.select("#side-menu a")
    ]

    links = get_additional_link(links)
    products = get_all_product_information(links)
    add_information_to_files(products)


def get_all_products() -> None:

    get_all_urls_for_parse()


if __name__ == "__main__":
    get_all_products()
