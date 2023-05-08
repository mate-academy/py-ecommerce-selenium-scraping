import csv
import requests

from bs4 import BeautifulSoup
from dataclasses import dataclass
from urllib.parse import urljoin

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement


BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


class WebDriver:
    def __enter__(self) -> object:
        self.driver = webdriver.Chrome()
        return self.driver

    def __exit__(
            self,
            exc_type: object,
            exc_value: object,
            traceback: object
    ) -> None:
        self.driver.quit()


def get_url(path: str = None, base_url: str = HOME_URL) -> str:
    if path:
        url = urljoin(base_url, path)
        return url
    return base_url


def parse_products(path=None):
    url = get_url(path)
    content = requests.get(url).content
    soup = BeautifulSoup(content, "html.parser")
    products_soup = soup.select(".thumbnail")
    return [parse_single_product(product) for product in products_soup]


def parse_single_product(product: BeautifulSoup) -> Product:
    title = product.select_one(".title")["title"],
    description = product.select_one(".description").text,
    price = float(product.select_one(".caption"
                                     ).text.split()[0].replace("$", "")
                  ),
    rating = int(product.select_one("p[data-rating]")["data-rating"]),
    num_of_reviews = int(product.select_one(".ratings").text.split()[0])
    return Product(
        title=title,
        description=description,
        price=price, rating=rating,
        num_of_reviews=num_of_reviews
    )


def parse_single_product_with_driver(product: WebElement) -> Product:
    title = product.find_element(
        By.CSS_SELECTOR, ".title").get_attribute("title"
                                                 )
    description = product.find_element(
        By.CSS_SELECTOR, ".description"
    ).text
    price = float(product.find_element(By.CSS_SELECTOR, ".caption"
                                       ).text.split()[0].replace("$", ""))
    rating = len(product.find_elements(
        By.CSS_SELECTOR, ".ratings span.glyphicon-star")
    )
    num_of_reviews = int(
        product.find_element(By.CSS_SELECTOR, ".ratings").text.split()[0]
    )
    return Product(
        title=title,
        description=description,
        price=price, rating=rating,
        num_of_reviews=num_of_reviews
    )


def get_product_with_pagination(driver: WebDriver,
                                endpoint: str):
    url = get_url(endpoint)
    driver.get(url)
    while True:
        try:
            button = driver.find_element(
                By.CSS_SELECTOR, ".ecomerce-items-scroll-more"
            )
            button.click()
        except Exception:
            products = driver.find_elements(
                By.CSS_SELECTOR, ".ecomerce-items .thumbnail"
            )
            return [
                parse_single_product_with_driver(product)
                for product in products
            ]


def write_products_to_csv(output_csv_path: str,
                          products: list[Product]) -> None:
    with open(output_csv_path, "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow((
            "title",
            "description",
            "price",
            "rating",
            "num_of_reviews"
        ))
        for product in products:
            writer.writerow(
                (
                    product.title,
                    product.description,
                    product.price,
                    product.rating,
                    product.num_of_reviews
                )
            )


def get_all_products() -> None:
    home = parse_products()
    write_products_to_csv("home.csv", home)

    computers = parse_products(path="computers")
    write_products_to_csv("computers.csv", computers)

    phones = parse_products(path="phones")
    write_products_to_csv("phones.csv", phones)

    with WebDriver() as driver:
        driver.get(HOME_URL)
        accept_cookies_button = driver.find_element(
            By.CLASS_NAME, "acceptCookies"
        )
        accept_cookies_button.click()

        touch = get_product_with_pagination(
            driver, endpoint="phones/touch"
        )
        write_products_to_csv("touch.csv", touch)

        laptops = get_product_with_pagination(
            driver, endpoint="computers/laptops"
        )
        write_products_to_csv("laptops.csv", laptops)

        tablets = get_product_with_pagination(
            driver, endpoint="computers/tablets"
        )
        write_products_to_csv("tablets.csv", tablets)


if __name__ == "__main__":
    get_all_products()
