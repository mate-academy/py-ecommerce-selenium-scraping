import csv
from dataclasses import dataclass
from urllib.parse import urljoin
from bs4 import BeautifulSoup, Tag
from selenium import webdriver
from selenium.webdriver.common.by import By
import requests
from selenium.webdriver.remote.webdriver import WebDriver


BASE_URL = "https://webscraper.io/"
HOME = urljoin(BASE_URL, "test-sites/e-commerce/more")
COMPUTERS = urljoin(BASE_URL, "test-sites/e-commerce/more/computers")
LAPTOPS = urljoin(BASE_URL, "test-sites/e-commerce/more/computers/laptops")
TABLETS = urljoin(BASE_URL, "test-sites/e-commerce/more/computers/tablets")
PHONES = urljoin(BASE_URL, "test-sites/e-commerce/more/phones")
TOUCH = urljoin(BASE_URL, "test-sites/e-commerce/more/phones/touch")

ALL_URLS = {
    HOME: "home",
    COMPUTERS: "computers",
    LAPTOPS: "laptops",
    TABLETS: "tablets",
    TOUCH: "touch",
    PHONES: "phones",
}

_driver: WebDriver | None = None


def get_driver() -> WebDriver:
    return _driver


def set_driver(new_driver: WebDriver) -> None:
    global _driver
    _driver = new_driver


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


def parse_single_product(product_soup: Tag) -> Product:
    return Product(
        title=product_soup.select_one(".title")["title"],
        description=product_soup.select_one(
            ".description").text.replace("\xa0", " "),
        price=float(product_soup.select_one(".price").text.replace("$", "")),
        rating=len(product_soup.select(".glyphicon-star")),
        num_of_reviews=int(
            product_soup.select_one(".ratings > p.pull-right").text.split()[0]
        ),
    )


def check_more_pages(page_soup: BeautifulSoup) -> str:
    more_pages = ""
    try:
        more_pages = page_soup.select_one(".ecomerce-items-scroll-more").text
    except AttributeError:
        pass
    return more_pages


def get_all_page_products(page_soup: BeautifulSoup) -> list:
    products = page_soup.select(".thumbnail")
    return [parse_single_product(product) for product in products]


def write_to_csv_file(products_to_write: list, file_name: str) -> None:
    with open(f"{file_name}.csv", "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow([
            "title",
            "description",
            "price",
            "rating",
            "num_of_reviews"
        ])
        writer.writerows(
            [[
                product.title,
                product.description,
                product.price,
                product.rating,
                product.num_of_reviews] for product in products_to_write]
        )


def get_all_products() -> None:
    for url, name in ALL_URLS.items():
        page = requests.get(url).content
        page_soup = BeautifulSoup(page, "html.parser")

        more_pages = check_more_pages(page_soup)
        if more_pages:
            driver = webdriver.Chrome()
            driver.implicitly_wait(0.5)
            driver.get(url)
            button = driver.find_element(
                By.CLASS_NAME,
                "ecomerce-items-scroll-more"
            )
            while button:
                button = driver.find_element(
                    By.CLASS_NAME,
                    "ecomerce-items-scroll-more"
                )

                driver.execute_script("arguments[0].click();", button)
                if button.get_attribute("style"):
                    new_page = driver.page_source
                    page_soup = BeautifulSoup(new_page, "html.parser")
                    driver.close()
                    break

        all_products = get_all_page_products(page_soup)
        write_to_csv_file(all_products, name)


if __name__ == "__main__":
    with webdriver.Chrome() as new_driver:
        set_driver(new_driver)
        get_all_products()
