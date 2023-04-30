import csv
from dataclasses import dataclass, fields, astuple
import time
from urllib.parse import urljoin
from bs4 import BeautifulSoup, Tag
from selenium import webdriver
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By


BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")
URLS = {
    "home": "test-sites/e-commerce/more",
    "computers": "test-sites/e-commerce/more/computers",
    "laptops": "test-sites/e-commerce/more/computers/laptops",
    "tablets": "test-sites/e-commerce/more/computers/tablets",
    "phones": "test-sites/e-commerce/more/phones",
    "touch": "test-sites/e-commerce/more/phones/touch"
}


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


PRODUCT_FIELD = [field.name for field in fields(Product)]


_driver: WebDriver | None


def get_driver() -> WebDriver:
    return _driver


def set_driver(new_driver: WebDriver) -> None:
    global _driver
    _driver = new_driver


def get_single_product(product_soup: Tag) -> Product:
    return Product(
        title=product_soup.select_one(".title")["title"],
        description=product_soup.select_one(
            ".description").text.replace("\xa0", " "),
        price=float(product_soup.select_one(
            ".price").text.replace("$", "")),
        rating=len(product_soup.select(".glyphicon-star")),
        num_of_reviews=int(product_soup.select_one(
            ".ratings > p.pull-right").text.split()[0]
                           ),
    )


def check_accept_cookies(driver: WebDriver) -> None:
    try:
        accept_cookies_button = driver.find_element(
            By.CLASS_NAME, "acceptCookies"
        )
        if accept_cookies_button:
            accept_cookies_button.click()
            time.sleep(0.1)
    except:
        pass


def check_more_pages(driver: WebDriver) -> None:
    try:
        more_button = driver.find_element(
            By.CLASS_NAME, "ecomerce-items-scroll-more"
        )
        if more_button:
            while more_button.value_of_css_property(
                    "display") == "block":
                more_button.click()
                time.sleep(0.1)
    except:
        pass


def get_page_of_product(url_product: str) -> [Product]:
    _driver = get_driver()
    url = urljoin(BASE_URL, url_product)
    _driver.get(url)

    check_accept_cookies(_driver)
    check_more_pages(_driver)

    page = _driver.page_source
    soup = BeautifulSoup(page, "html.parser")

    products = soup.select(".thumbnail")
    return [get_single_product(product_) for product_ in products]


def write_products_in_csv_file() -> None:
    for key, value in URLS.items():
        products = get_page_of_product(str(value))
        output_csv_path = str(key) + ".csv"
        with open(
                output_csv_path,
                "w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(PRODUCT_FIELD)
            writer.writerows([astuple(product_) for product_ in products])


def get_all_products() -> [Product]:
    with webdriver.Chrome() as new_driver:
        set_driver(new_driver)
        write_products_in_csv_file()


if __name__ == "__main__":
    get_all_products()
