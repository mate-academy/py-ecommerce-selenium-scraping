import csv
import time
from dataclasses import dataclass

from urllib.parse import urljoin
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from bs4 import BeautifulSoup, Tag
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")
URLS = {
    "home": HOME_URL,
    "computers": urljoin(HOME_URL, "computers"),
    "laptops": urljoin(HOME_URL, "computers/laptops"),
    "tablets": urljoin(HOME_URL, "computers/tablets"),
    "phones": urljoin(HOME_URL, "phones"),
    "touch": urljoin(HOME_URL, "phones/touch")
}


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


def click_more_button(url: str, driver: WebDriver) -> list:
    driver.get(url)
    more_button = None
    try:
        driver.find_element(By.CLASS_NAME, "acceptCookies").click()
    except Exception as error:
        print(error)
    try:
        more_button = driver.find_element(
            By.CLASS_NAME,
            "ecomerce-items-scroll-more"
        )
    except Exception as error:
        print(error)

    if more_button is not None:
        while more_button.is_displayed():
            more_button.click()
            time.sleep(1)

    soup = BeautifulSoup(driver.page_source, "html.parser")
    products = soup.select(".thumbnail")
    return [parse_single_product(product) for product in products]


def parse_single_product(product_soup: Tag) -> Product:
    return Product(
        title=product_soup.select_one(".title")["title"],
        description=product_soup.select_one(
            ".description").text.replace("\xa0", " "),
        price=float(product_soup.select_one(".price").text.replace("$", "")),
        rating=len(product_soup.select("span.glyphicon-star")),
        num_of_reviews=int(product_soup.select_one(
            ".ratings > p.pull-right"
        ).text.split()[0])
    )


def get_all_products() -> None:
    chrome_options = Options()

    driver = webdriver.Chrome(options=chrome_options)

    with driver as driver:
        for title, url in URLS.items():
            products = click_more_button(url, driver)
            write_data_to_csv(products, f"{title}.csv")


def write_data_to_csv(products: list[Product], file_name: str) -> None:
    with open(file_name, "w", encoding="utf-8") as file:
        csv_file = csv.writer(file)
        csv_file.writerow(
            [
                "title",
                "description",
                "price",
                "rating",
                "num_of_reviews",
            ]
        )
        for product in products:
            csv_file.writerow(
                [
                    product.title,
                    product.description,
                    product.price,
                    product.rating,
                    product.num_of_reviews,
                ]
            )


if __name__ == "__main__":
    get_all_products()
