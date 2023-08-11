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


def parse_single_product(product: Tag) -> Product:
    return Product(
        title=product.select_one(".title")["title"],
        description=product.select_one(
            ".description"
        ).text.replace("\xa0", " "),
        price=float(product.select_one(".price").text.replace("$", "")),
        rating=len(product.select(".ratings span")),
        num_of_reviews=int(
            product.select_one("p.pull-right").text.split()[0]
        )
    )


def accept_cookies(driver: WebDriver) -> None:
    cookies_button = driver.find_elements(By.CLASS_NAME, "acceptCookies")
    if cookies_button:
        cookies_button[0].click()


def click_more_button(driver: WebDriver) -> None:
    more_button = driver.find_elements(
        By.CLASS_NAME, "ecomerce-items-scroll-more"
    )

    if more_button:
        while more_button[0].is_displayed():
            more_button[0].click()
            time.sleep(0.1)


def get_products_for_page(page_url: str, driver: WebDriver) -> list[Product]:
    driver.get(page_url)
    accept_cookies(driver)
    click_more_button(driver)

    page = driver.page_source
    page_soup = BeautifulSoup(page, "html.parser")

    products = page_soup.select(".thumbnail")

    return [parse_single_product(product) for product in products]


def write_products_to_csv(
        products: list[Product],
        output_csv_path: str
) -> None:
    with open(output_csv_path, "w") as file:
        writer = csv.writer(file)
        writer.writerow(PRODUCT_FIELDS)
        writer.writerows([astuple(product) for product in products])


def get_all_products() -> None:
    with webdriver.Chrome() as driver:
        for page_name, page_url in URLS.items():
            products = get_products_for_page(page_url, driver)
            output_csv_path = f"{page_name}.csv"
            write_products_to_csv(products, output_csv_path)
            print(f"Scraped {len(products)} products from {page_name},"
                  f"saved to {output_csv_path}")


if __name__ == "__main__":
    get_all_products()
