import csv
from dataclasses import dataclass, fields, astuple
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from selenium.common import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium import webdriver
from selenium.webdriver.remote.webelement import WebElement

from app.driver import ChromeDriver

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")

PRODUCT_PAGES = {
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


def find_element(
    by: str,
    value: str,
    driver: webdriver.Chrome
) -> WebElement | None:
    try:
        element = driver.find_element(by, value)
        return element
    except NoSuchElementException:
        return None


def handle_more_button(driver: webdriver.Chrome) -> None:
    button = find_element(
        By.CSS_SELECTOR,
        'a.ecomerce-items-scroll-more:not([style*="none"])',
        driver
    )
    while button:
        if button.is_enabled() and button.is_displayed():
            driver.execute_script(
                "arguments[0].click();", button
            )
        else:
            break


def parse_single_product(product_soup: BeautifulSoup) -> Product:
    return Product(
        title=product_soup.select_one("a.title")["title"],
        description=product_soup.select_one(
            "p.description"
        ).text.replace("\xa0", " "),
        price=float(product_soup.select_one("h4.price").text.replace("$", "")),
        rating=len(product_soup.select(".ws-icon-star")),
        num_of_reviews=int(product_soup.select_one(
            "p.review-count"
        ).text.split()[0]),
    )


def write_to_csv(products: list[Product], file_name: str) -> None:
    with open(file_name, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(PRODUCT_FIELDS)
        writer.writerows([astuple(product) for product in products])


def parse_page(url: str) -> list[Product]:
    driver = ChromeDriver().web_driver
    driver.get(url)

    while True:
        more_button = find_element(
            By.CSS_SELECTOR,
            'a.ecomerce-items-scroll-more:not([style*="none"])',
            driver
        )
        if more_button:
            handle_more_button(driver)

        break

    products_soup = BeautifulSoup(
        driver.page_source, "html.parser"
    ).select(".card.product-wrapper")

    products = []

    for product_soup in products_soup:
        products.append(
            parse_single_product(product_soup)
        )

    return products


def get_all_products() -> None:
    try:
        for page_name, page_url in PRODUCT_PAGES.items():
            products = parse_page(page_url)
            write_to_csv(products, f"{page_name}.csv")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    get_all_products()
