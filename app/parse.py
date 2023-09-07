import csv
from dataclasses import dataclass, fields, astuple
from urllib.parse import urljoin
from bs4 import BeautifulSoup, Tag
from selenium import webdriver
from selenium.common import NoSuchElementException
from selenium.webdriver.common.by import By


BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")
PATHS_URLS = [
    [HOME_URL, "home.csv"],
    [HOME_URL + "computers/laptops", "laptops.csv"],
    [HOME_URL + "computers/tablets", "tablets.csv"],
    [HOME_URL + "phones", "phones.csv"],
    [HOME_URL + "phones/touch", "touch.csv"],
    [HOME_URL + "computers", "computers.csv"],
]


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


PRODUCT_FIELDS = [field.name for field in fields(Product)]


def parse_single_product(product_soup: Tag) -> Product:
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


def accept_cookies(driver: webdriver) -> None:
    try:
        cookie_btn = driver.find_element(
            By.CLASS_NAME, "acceptCookies"
        )
        cookie_btn.click()
    except NoSuchElementException:
        pass


def more_button(url: str) -> BeautifulSoup:
    driver = webdriver.Chrome()
    driver.get(url)
    accept_cookies(driver)

    try:
        more = driver.find_element(By.CLASS_NAME, "ecomerce-items-scroll-more")

        while more and more.is_displayed():
            more.click()
    except NoSuchElementException:
        pass

    finally:
        return BeautifulSoup(driver.page_source, "html.parser")


def parse_pages(url: str) -> list[Product]:
    soup = more_button(url)
    products_info = soup.select(".thumbnail")
    return [parse_single_product(product) for product in products_info]


def write_to_csv(path: str, products: list[Product]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(PRODUCT_FIELDS)
        writer.writerows([astuple(product) for product in products])


def get_all_products() -> None:
    for path, url in PATHS_URLS:
        products = parse_pages(url)
        write_to_csv(path, products)


if __name__ == "__main__":
    get_all_products()
