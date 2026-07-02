import csv
from dataclasses import fields, astuple, dataclass
from urllib.parse import urljoin

from bs4 import Tag, BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.webdriver import WebDriver

from app.utils import close_cookies_banner, click_show_more_until_gone

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


PRODUCT_FIELDS = [field.name for field in fields(Product)]

PAGES = {
    "home": HOME_URL,
    "computers": urljoin(BASE_URL, "test-sites/e-commerce/more/computers"),
    "laptops": urljoin(
        BASE_URL,
        "test-sites/e-commerce/more/computers/laptops"
    ),
    "tablets": urljoin(
        BASE_URL,
        "test-sites/e-commerce/more/computers/tablets"
    ),
    "phones": urljoin(BASE_URL, "test-sites/e-commerce/more/phones"),
    "touch": urljoin(BASE_URL, "test-sites/e-commerce/more/phones/touch"),
}


def parse_product(product: Tag) -> Product:
    return Product(
        title=product.select_one(".title")["title"],
        description=product.select_one(
            ".description"
        ).text.replace("\xa0", " "),
        price=float(product.select_one(".price").text.replace("$", "")),
        rating=len(product.select(".ws-icon.ws-icon-star")),
        num_of_reviews=int(product.select_one(".review-count").text.split()[0])
    )


def get_products_by_url(driver: WebDriver, url: str) -> list[Product]:
    driver.get(url)
    click_show_more_until_gone(driver)

    soup = BeautifulSoup(driver.page_source, "html.parser")
    products = soup.select(".card-body")

    return [parse_product(product) for product in products]


def write_products_to_csv(
        products: list[Product],
        output_csv_path: str
) -> None:
    with open(output_csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(PRODUCT_FIELDS)
        writer.writerows([astuple(product) for product in products])


def get_all_products() -> None:
    with webdriver.Chrome() as driver:
        driver.get(HOME_URL)
        close_cookies_banner(driver)

        for page_name, url in PAGES.items():
            products = get_products_by_url(driver, url)
            write_products_to_csv(products, f"{page_name}.csv")


if __name__ == "__main__":
    get_all_products()
