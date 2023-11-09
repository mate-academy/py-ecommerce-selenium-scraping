import csv
import time

from selenium.webdriver import Chrome
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup, Tag
from dataclasses import dataclass, fields, astuple
from urllib.parse import urljoin


BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")

URLS = {
    "home": HOME_URL,
    "computers": urljoin(HOME_URL, "computers"),
    "laptops": urljoin(HOME_URL, "computers/laptops"),
    "tablets": urljoin(HOME_URL, "computers/tablets"),
    "phones": urljoin(HOME_URL, "phones"),
    "touch": urljoin(HOME_URL, "phones/touch"),
}


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


PRODUCT_FIELDS = [field.name for field in fields(Product)]


def get_driver() -> Chrome:
    options = Options()
    options.add_argument("--headless")
    driver = Chrome(options=options)
    return driver


def parse_single_product(product_soup: Tag) -> Product:
    return Product(
        title=product_soup.select_one(".title")["title"],
        description=product_soup.select_one(".description").text,
        price=float(product_soup.select_one(".price").text.replace("$", "")),
        rating=len(product_soup.select(".ratings span")),
        num_of_reviews=int(product_soup.select_one(
            ".review-count"
        ).text.split()[0]),
    )


def get_page_products(page_url: str, driver: WebDriver) -> [Product]:

    driver.get(page_url)

    cookies = driver.find_elements(By.CLASS_NAME, "acceptCookies")
    if cookies:
        cookies[0].click()

    button_more = driver.find_elements(
        By.CLASS_NAME, "ecomerce-items-scroll-more"
    )
    if button_more:
        button_more = button_more[0]
        while button_more.is_displayed():
            button_more.click()
            time.sleep(1)

    soup = BeautifulSoup(driver.page_source, "html.parser")

    products = soup.select(".thumbnail")
    return [parse_single_product(product_soup) for product_soup in products]


def write_products_to_csv(products: [Product], path: str) -> None:
    with open(f"{path}.csv", "w", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(PRODUCT_FIELDS)
        writer.writerows(astuple(product) for product in products)


def get_all_products() -> None:
    with get_driver() as driver:
        for file_name, url in URLS.items():
            products = get_page_products(url, driver)
            write_products_to_csv(products=products, path=file_name)


if __name__ == "__main__":
    get_all_products()
