import csv
import logging
import sys

from dataclasses import dataclass, fields, astuple
from urllib.parse import urljoin
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException

from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup


BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")
PRODUCTS_PAGES = {
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

    @classmethod
    def parse_single_product(cls, product_soup: BeautifulSoup) -> "Product":
        return cls(
            title=product_soup.select_one(".title")["title"],
            description=product_soup.select_one(
                ".description"
            ).text.strip().replace("\xa0", " "),
            price=float(product_soup.select_one(".price").text.strip("$")),
            rating=len(
                product_soup.find_all("span", class_="ws-icon ws-icon-star")
            ),
            num_of_reviews=int(
                product_soup.select_one(
                    "div.ratings > p.review-count"
                ).text.split()[0]
            ),
        )


def load_more(driver: webdriver.Chrome) -> None:
    while True:
        try:
            button = driver.find_element(
                By.CLASS_NAME,
                "ecomerce-items-scroll-more"
            )
            if button.is_displayed():
                ActionChains(driver).click(button).perform()
            else:
                break
        except NoSuchElementException:
            break


def get_page_products(driver: webdriver.Chrome, url: str) -> [Product]:
    driver.get(url)
    accept_cookies(driver)
    load_more(driver)
    soup = BeautifulSoup(driver.page_source, "html.parser")
    return [
        Product.parse_single_product(product)
        for product in soup.select(".thumbnail")
    ]


def accept_cookies(driver: webdriver.Chrome) -> None:
    try:
        accept_cookies_button = driver.find_element(
            By.CLASS_NAME,
            "acceptContainer"
        )
        accept_cookies_button.click()
        logging.info("Cookie banner accepted")
    except NoSuchElementException:
        logging.info("Cookies banner not found")


def write_products_to_csv(file_name: str, products: [Product]) -> None:
    with open(file_name, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow([field.name for field in fields(Product)])
        writer.writerows([astuple(product) for product in products])
    logging.info(f"Products saved to {file_name}")


def get_all_products() -> None:
    with webdriver.Chrome() as driver:
        for page_name, url in PRODUCTS_PAGES.items():
            logging.info(f"Start parsing {page_name} page")
            products = get_page_products(driver, url)
            write_products_to_csv(f"{page_name}.csv", products)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="[%(levelname)8s]: %(message)s",
        handlers=[
            logging.FileHandler("parser.log"),
            logging.StreamHandler(sys.stdout),
        ],
    )
    get_all_products()
