import csv
import time
from dataclasses import dataclass, fields, astuple
from urllib.parse import urljoin

from bs4 import BeautifulSoup, Tag
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")
PHONES_URL = urljoin(HOME_URL, "phones/")
TOUCHES_URL = urljoin(PHONES_URL, "touch")
COMPUTERS_URL = urljoin(HOME_URL, "computers/")
LAPTOPS_URL = urljoin(COMPUTERS_URL, "laptops")
TABLETS_URL = urljoin(COMPUTERS_URL, "tablets")

URL_TO_PARSE_REQUESTS = {
    HOME_URL: "home.csv",
    PHONES_URL: "phones.csv",
    COMPUTERS_URL: "computers.csv",
}

URL_TO_PARSE_SELENIUM = {
    TOUCHES_URL: "touch.csv",
    LAPTOPS_URL: "laptops.csv",
    TABLETS_URL: "tablets.csv",
}

_driver: WebDriver | None = None


def get_driver() -> WebDriver:
    return _driver


def set_driver(driver: WebDriver) -> None:
    global _driver
    _driver = driver


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


PRODUCT_FIELDS = [field.name for field in fields(Product)]


def parse_single_product_request(soup: Tag) -> Product:
    return Product(
        title=soup.select_one(".title")["title"],
        description=soup.select_one(".description").text,
        price=float(soup.select_one(".price").text.replace("$", "")),
        rating=int(soup.select_one("p[data-rating]")["data-rating"]),
        num_of_reviews=int(soup.select_one(".review-count").text.split()[0]),
    )


def parse_single_product_selenium(product: WebElement) -> Product:
    return Product(
        title=product.find_element(
            By.CLASS_NAME,
            "title"
        ).get_property("title"),
        description=product.find_element(By.CLASS_NAME, "description").text,
        price=float(product.find_element(
            By.CLASS_NAME,
            "price"
        ).text.replace("$", "")),
        rating=len(product.find_elements(By.CLASS_NAME, "ws-icon")),
        num_of_reviews=int(product.find_element(
            By.CLASS_NAME,
            "review-count"
        ).text.split()[0]),
    )


def parse_page_with_selenium() -> None:
    for url, file_name in URL_TO_PARSE_SELENIUM.items():
        driver = get_driver()
        driver.get(url)
        while True:
            more_button = driver.find_element(
                By.CLASS_NAME,
                "ecomerce-items-scroll-more"
            )
            time.sleep(0.5)
            if more_button.value_of_css_property("display") == "inline-block":
                try:
                    more_button.click()
                except Exception as e:
                    print(e)
            else:
                products = driver.find_elements(By.CLASS_NAME, "card-body")
                write_products_to_csv(
                    file_name,
                    [
                        parse_single_product_selenium(product)
                        for product in products
                    ]
                )
                break


def parse_page_with_request() -> None:
    for url, file_name in URL_TO_PARSE_REQUESTS.items():
        response = requests.get(url).content
        page_soup = BeautifulSoup(response, "html.parser")
        products = page_soup.select(".card-body")
        write_products_to_csv(
            file_name,
            [parse_single_product_request(product) for product in products]
        )


def get_all_products() -> None:
    parse_page_with_request()

    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    with webdriver.Chrome(options=chrome_options) as driver:
        set_driver(driver)
        parse_page_with_selenium()


def write_products_to_csv(output_csv_path: str, products: [Product]) -> None:
    with open(
            f"{output_csv_path}",
            "w",
            encoding="utf-8",
            newline=""
    ) as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(PRODUCT_FIELDS)
        writer.writerows([astuple(product) for product in products])


if __name__ == "__main__":
    get_all_products()
