import csv
from dataclasses import dataclass, fields, astuple
from urllib.parse import urljoin

from bs4 import BeautifulSoup, Tag
from selenium.common import NoSuchElementException
from selenium.webdriver.common.by import By

from app.driver_singleton import WebDriverSingleton

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")
COMPUTERS_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/computers")
PHONES_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/phones")
TOUCH_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/phones/touch")
LAPTOP_URLS = urljoin(BASE_URL, "test-sites/e-commerce/more/computers/laptops")
TABLETS_URLS = urljoin(
    BASE_URL,
    "test-sites/e-commerce/more/computers/tablets"
)


URLS_TO_PARSE = {
    "home": HOME_URL,
    "computers": COMPUTERS_URL,
    "phones": PHONES_URL,
    "touch": TOUCH_URL,
    "laptops": LAPTOP_URLS,
    "tablets": TABLETS_URLS
}


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


PRODUCT_FIELDS = [field.name for field in fields(Product)]


def parse_single_product(product: Tag) -> Product:
    stars_count = len(product.select(".ratings .ws-icon-star"))

    return Product(
        title=(product.select_one(selector=".title")["title"]),
        description=product.select_one(selector=".description").text.replace(
            "\xa0", " "
        ),
        price=float(
            product.select_one(selector=".price").text.strip().replace("$", "")
        ),
        rating=stars_count,
        num_of_reviews=int(
            product.select_one(
                selector=".review-count").text.strip().split()[0]
        ),
    )


def get_products_soup(url: str) -> list:
    """Returns card bodies for all products on the specific page"""
    driver = WebDriverSingleton().get_driver()
    driver.get(url=url)
    try:
        cookies_button = driver.find_element(By.CLASS_NAME, "acceptCookies")
        if cookies_button.is_displayed():
            driver.execute_script("arguments[0].click();", cookies_button)
    except NoSuchElementException:
        pass

    try:
        next_button = driver.find_element(
            By.CLASS_NAME,
            "ecomerce-items-scroll-more"
        )
        while next_button.is_displayed():
            driver.execute_script("arguments[0].click();", next_button)
    except NoSuchElementException:
        pass

    return BeautifulSoup(driver.page_source, "html.parser").select(
        selector=".card-body"
    )


def parse_all_products_from_specific_url(url: str) -> list:
    """Gets card-bodies and returns list of Product instances"""
    products_from_specific_url = []
    products_soup = get_products_soup(url=url)
    for product in products_soup:
        products_from_specific_url.append(parse_single_product(product))

    return products_from_specific_url


def write_products_to_csv(file_name: str, products: list[Product]) -> None:
    with open(f"{file_name}.csv", "w") as destination_csv:
        writer = csv.writer(destination_csv)
        writer.writerow(PRODUCT_FIELDS)
        writer.writerows([astuple(product) for product in products])


def get_all_products() -> None:
    for file_name, url in URLS_TO_PARSE.items():
        products = parse_all_products_from_specific_url(url=url)
        write_products_to_csv(file_name, products)


if __name__ == "__main__":
    get_all_products()
