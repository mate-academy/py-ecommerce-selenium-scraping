import csv
import logging
import time
import sys

from dataclasses import dataclass, astuple, fields
from bs4 import Tag, BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from tqdm import tqdm
from typing import Self
from urllib.parse import urljoin


BASE_URL = "https://webscraper.io/test-sites/e-commerce/more/"
URLS = {
    "home": BASE_URL,
    "computers": urljoin(BASE_URL, "computers/"),
    "laptops": urljoin(BASE_URL, "computers/laptops"),
    "tablets": urljoin(BASE_URL, "computers/tablets"),
    "phones": urljoin(BASE_URL, "phones/"),
    "touch": urljoin(BASE_URL, "phones/touch")
}


logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)8s]: %(message)s",
    handlers=[
        logging.FileHandler("parser.log"),
        logging.StreamHandler(sys.stdout),
    ],
)


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int

    @classmethod
    def parse_single_product(cls, product: Tag) -> Self:
        single_product_data = dict(
            title=product.select_one(".title")["title"],
            description=product.select_one(
                ".description"
            ).text.replace("\xa0", " "),
            price=float(product.select_one(".price").text.replace("$", "")),
            rating=len(product.select(".ws-icon-star")),
            num_of_reviews=int(
                product.select_one("p.pull-right").text.split()[0]
            ),
        )
        return cls(**single_product_data)


def parse_single_page(page_url: str, driver: WebDriver) -> list[Product]:
    driver.get(page_url)

    cookies = driver.find_elements(By.CLASS_NAME, "acceptCookies")
    if cookies:
        cookies[0].click()

    button_more = driver.find_elements(
        By.CLASS_NAME,
        "ecomerce-items-scroll-more",
    )
    if button_more:
        while button_more[0].is_displayed():
            button_more[0].click()
            time.sleep(0.3)

    page_soup = BeautifulSoup(driver.page_source, "html.parser")
    page_products_soup = page_soup.select(".thumbnail")
    all_page_products = [
        Product.parse_single_product(product)
        for product in page_products_soup
    ]

    return all_page_products


def write_data_to_csv(
        products: list[Product],
        output_csv_path: str,
) -> None:
    with open(output_csv_path, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow([field.name for field in fields(Product)])
        writer.writerows([astuple(product) for product in products])


def get_all_products() -> None:
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')

    with webdriver.Chrome(options=options) as driver:
        logging.info(
            "Start parsing process\n________________________________\n"
        )

        for name, url in tqdm(URLS.items(), desc="Parsing URLs"):
            logging.info(f"Parsing '{url}' page")
            products = parse_single_page(url, driver)
            file_name = f"{name}.csv"
            logging.info(f"Writing data to '{file_name}'")
            write_data_to_csv(products, file_name)

    logging.info(
        "\n________________________________\n"
        "Parsing is finished successfully"
        "\n________________________________\n"
    )


if __name__ == "__main__":
    get_all_products()
