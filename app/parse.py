import csv
from dataclasses import astuple, fields
from typing import List

from selenium import webdriver
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
from selenium.webdriver.firefox.webdriver import WebDriver

from app.constants import COMPLEX_URL, SIMPLE_URLS
from app.models import Product


PRODUCT_FIELDS = [field.name for field in fields(Product)]


def parse_single_product(product_soup: BeautifulSoup) -> Product:
    return Product(
        title=product_soup.select_one(".title")["title"],
        description=product_soup.select_one(".description")
        .text.replace("\xa0", " "),
        price=float(product_soup.select_one(".price").text.replace("$", "")),
        rating=len(product_soup.select(".ratings span.ws-icon.ws-icon-star")),
        num_of_reviews=int(
            product_soup.select_one(".review-count").text.split()[0]
        ),
    )


def fetch_and_parse_products(
        driver: WebDriver,
        url: str,
        with_pagination: bool
) -> List[Product]:

    driver.get(url)

    if with_pagination:
        while True:
            try:
                more_button = driver.find_element(
                    By.CLASS_NAME,
                    "ecomerce-items-scroll-more"
                )
                more_button.click()
            except Exception as e:
                print(e)
                break

    page_soup = BeautifulSoup(
        driver.page_source,
        "html.parser").select(".thumbnail")

    return [parse_single_product(product_soup) for product_soup in page_soup]


def write_to_csv(all_products: [Product], path_to_csv: str) -> None:
    with open(
            f"{path_to_csv}.csv", "w",
            newline="",
            encoding="utf-8"
    ) as csv_file:

        writer = csv.writer(csv_file)
        writer.writerow(PRODUCT_FIELDS)
        writer.writerows([astuple(product) for product in all_products])


def process_urls(
        driver: WebDriver,
        urls: List[str],
        with_pagination: bool
) -> None:
    for url in urls:
        path_to_csv = url.split("/")[-1] if with_pagination \
            else url.split("/")[-2].replace("more", "home")
        products = fetch_and_parse_products(driver, url, with_pagination)
        write_to_csv(products, path_to_csv)


def get_all_products() -> None:
    with webdriver.Firefox() as driver:
        process_urls(driver, SIMPLE_URLS, with_pagination=False)
        process_urls(driver, COMPLEX_URL, with_pagination=True)


if __name__ == "__main__":
    get_all_products()
