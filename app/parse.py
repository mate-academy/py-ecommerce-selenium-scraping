import csv
import sys
import time

import requests
import logging
from dataclasses import dataclass, fields, astuple
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from urllib.parse import urljoin
from bs4 import BeautifulSoup, Tag
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from tqdm import tqdm


BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")


_driver: WebDriver | None = None


def get_driver() -> WebDriver:
    return _driver


def set_driver(new_driver: WebDriver) -> None:
    global _driver
    _driver = new_driver


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


PRODUCT_FIELDS = [field.name for field in fields(Product)]


logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)8s]: %(message)s",
    handlers=[logging.FileHandler("parser.log"),
              logging.StreamHandler(sys.stdout)
              ],
)


def get_pages_to_parse() -> dict:
    content = requests.get(HOME_URL).content
    soup = BeautifulSoup(content, "html.parser")
    side_menu = soup.select_one("#side-menu")
    nav_links = side_menu.select(".nav-link")
    pages_dict = {
        urljoin(BASE_URL, nav_link["href"]): nav_link.select_one("span").text
        for nav_link in nav_links
    }
    secondary_pages_dict = {}
    for link in pages_dict.keys():
        new_content = requests.get(link).content
        new_soup = BeautifulSoup(new_content, "html.parser")
        side_menu_second_level = new_soup.select_one(".nav-second-level")
        if side_menu_second_level:
            second_level_nav_links = side_menu_second_level.select(".nav-link")
            secondary_pages_dict.update(
                {
                    urljoin(BASE_URL, nav_link["href"]): nav_link.select_one(
                        "span"
                    ).text
                    for nav_link in second_level_nav_links
                }
            )
    pages_dict.update(secondary_pages_dict)
    return pages_dict


def parse_single_product(product: Tag) -> Product:
    return Product(
        title=product.select_one(".title")["title"],
        description=product.select_one(".description")
        .get_text(strip=True)
        .replace("\xa0", " "),
        price=float(product.select_one(".price").text.replace("$", "")),
        rating=len(product.select(".ratings .ws-icon-star")),
        num_of_reviews=int(product
                           .select_one(".review-count")
                           .text
                           .split()[0]),
    )


def get_single_page_products(url: str) -> list[Product]:
    logging.info(f"start parsing page {url}")
    driver = get_driver()
    driver.get(url)
    wait = WebDriverWait(driver, 10)
    while True:
        more_buttons = driver.find_elements(
            By.CLASS_NAME, "ecomerce-items-scroll-more"
        )
        if not more_buttons:
            break
        more_button = more_buttons[0]
        if not more_button.is_displayed():
            break

        driver.execute_script(
            "arguments[0].scrollIntoView({block: 'center'});", more_button
        )

        try:
            wait.until(
                ec.element_to_be_clickable(
                    (By.CLASS_NAME, "ecomerce-items-scroll-more")
                )
            )
            more_button.click()
            time.sleep(1)
        except Exception:
            break
    page_source = driver.page_source
    soup = BeautifulSoup(page_source, "html.parser")
    products = soup.select(".card-body")
    return [parse_single_product(product) for product in products]


def write_to_csv(products: list[Product], page_name: str) -> None:
    with open(f"{page_name}.csv", "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(PRODUCT_FIELDS)
        writer.writerows(astuple(product) for product in products)


def get_all_products() -> None:
    options = Options()
    options.add_argument("--headless")
    with webdriver.Chrome(options=options) as driver:
        set_driver(driver)
        pages = get_pages_to_parse()
        for url, page_name in tqdm(pages.items()):
            time.sleep(1)
            all_products = get_single_page_products(url)
            write_to_csv(all_products, page_name.lower())
    return None


if __name__ == "__main__":
    get_all_products()
