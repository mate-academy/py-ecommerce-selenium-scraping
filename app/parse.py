import csv
import time
from dataclasses import dataclass, fields, astuple
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

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

_driver: WebDriver | None = None


def get_driver() -> WebDriver:
    return _driver


def set_driver(new_driver: WebDriver) -> None:
    global _driver
    _driver = new_driver


def parse_single_product(product_soup: BeautifulSoup) -> Product:
    return Product(
        title=product_soup.select_one(".title")["title"],
        description=product_soup.select_one(".description").text.replace(
            "\xa0", " "
        ),
        price=float(product_soup.select_one(".price").text.replace("$", "")),
        rating=len(product_soup.select(".ws-icon-star")),
        num_of_reviews=int(
            product_soup.select_one(
                ".ratings > p.review-count"
            ).text.split()[0]
        ),
    )


def get_all_products_from_page(link: str) -> list:
    driver = get_driver()
    driver.get(link)

    cookies_button = driver.find_elements(By.CLASS_NAME, "acceptCookies")
    if cookies_button:
        driver.implicitly_wait(2)
        cookies_button[0].click()

    more_button = driver.find_elements(
        By.CLASS_NAME, "ecomerce-items-scroll-more"
    )
    if more_button:
        more_button = more_button[0]
        while more_button.is_displayed():
            more_button.click()
            time.sleep(1)

    page_soup = BeautifulSoup(driver.page_source, "html.parser")

    products = page_soup.select(".thumbnail")

    return [parse_single_product(product_soup) for product_soup in products]


def get_links_from_side_menu() -> list[str]:
    driver = get_driver()
    driver.get(HOME_URL)

    side_menu = driver.find_element(By.ID, "side-menu")
    elements = side_menu.find_elements(By.CSS_SELECTOR, "[href]")
    links = [element.get_attribute("href") for element in elements]

    sub_links = []

    for link in links:
        driver.get(link)

        second_level_links = driver.find_elements(
            By.CLASS_NAME, "subcategory-link"
        )
        if second_level_links:
            for second_level_link in second_level_links:
                sub_links.append(second_level_link.get_attribute("href"))

    links.extend(sub_links)

    return links


def create_file_titles_for_each_link(links: list[str]) -> dict:
    file_titles = {}

    for link in links:
        title = link.split("/")[-1] + ".csv"

        if title == "more.csv":
            title = "home.csv"

        file_titles[title] = link

    return file_titles


def write_products_to_csv(csv_path: str, products: [Product]) -> None:
    with open(csv_path, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(PRODUCT_FIELDS)
        writer.writerows([astuple(product) for product in products])


def get_all_products() -> None:
    with webdriver.Chrome() as new_driver:
        set_driver(new_driver)

        links = get_links_from_side_menu()
        links_with_titles = create_file_titles_for_each_link(links)

        for title, link in links_with_titles.items():
            products = get_all_products_from_page(link)

            write_products_to_csv(title, products)


if __name__ == "__main__":
    get_all_products()
