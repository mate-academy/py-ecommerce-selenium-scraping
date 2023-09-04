from dataclasses import dataclass, astuple, fields
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common import NoSuchElementException
import csv


BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")
PRODUCTS_URLS = {
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


def parse_single_product(product_soup: BeautifulSoup) -> Product:
    return Product(
        title=product_soup.select_one(".title")["title"],
        description=product_soup.select_one(
            ".description"
        ).text.replace("\xa0", " "),
        price=float(product_soup.select_one(".price").text.replace("$", "")),
        rating=len(product_soup.select(".ws-icon.ws-icon-star")),
        num_of_reviews=int(
            product_soup.select_one("p.pull-right").text.split()[0]
        )
    )


def more_button(url: str) -> BeautifulSoup:
    driver = webdriver.Chrome()
    driver.get(url)

    try:
        more = driver.find_element(By.CLASS_NAME, "ecomerce-items-scroll-more")
    except NoSuchElementException:
        more = None

    while more:
        style_value = more.get_attribute("style")
        if "display: none;" in style_value:
            break
        driver.execute_script("arguments[0].click();", more)

    return BeautifulSoup(driver.page_source, "html.parser")


def parse_pages(url: str) -> list[Product]:
    soup = more_button(url)
    products_info = soup.select(".thumbnail")
    return [parse_single_product(product) for product in products_info]


def write_to_csv(category: str, products: list[Product]) -> None:
    with open(
            f"{category}.csv",
            "w",
            newline="",
            encoding="utf-8"
    ) as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow([field.name for field in fields(Product)])
        writer.writerows([astuple(product) for product in products])


def get_all_products() -> None:
    for category, url in PRODUCTS_URLS.items():
        products = parse_pages(url)
        write_to_csv(category, products)


if __name__ == "__main__":
    get_all_products()
