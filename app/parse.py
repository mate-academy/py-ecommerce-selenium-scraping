import csv
import time
from dataclasses import dataclass
from urllib.parse import urljoin
from selenium.webdriver.support import expected_conditions as ec
from bs4 import BeautifulSoup
from selenium.common import (
    NoSuchElementException,
    StaleElementReferenceException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")
PRODUCT_FIELDS = ["title", "description", "price", "rating", "num_of_reviews"]


class Driver:
    def __init__(self) -> None:
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        self.driver = webdriver.Chrome(options=chrome_options)

    def closed(self) -> None:
        self.driver.quit()


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


def click_button_more(browser: Driver) -> str:
    while True:
        updated_html = browser.driver.page_source
        try:
            button = browser.driver.find_element(
                By.CSS_SELECTOR, "a.ecomerce-items-scroll-more"
            )
            if button.is_displayed():
                browser.driver.execute_script(
                    "arguments[0].scrollIntoView(true);", button
                )
                browser.driver.execute_script("arguments[0].click();", button)
                WebDriverWait(browser.driver, 10).until(
                    ec.presence_of_element_located(
                        (
                            By.CSS_SELECTOR,
                            "div.ecomerce-items[data-type='more']",
                        )
                    )
                )
                time.sleep(1)
            else:
                break
        except (NoSuchElementException, StaleElementReferenceException):
            break
    return updated_html


def side_bar_buttons(browser: Driver) -> list[str]:
    categories = browser.driver.find_elements(
        By.CSS_SELECTOR, "#side-menu > li > a"
    )
    category_links = [
        category.get_attribute("href") for category in categories
    ]
    return category_links


def subcategory_buttons(browser: Driver) -> list[str]:
    categories = side_bar_buttons(browser)
    subcategory_links = []
    for category in categories:
        browser.driver.get(category)
        subcategory = browser.driver.find_elements(
            By.CSS_SELECTOR, ".nav-second-level > li > a"
        )
        subcategory_links.extend(
            [link.get_attribute("href") for link in subcategory]
        )
    return subcategory_links


def parse_all_products(browser: Driver) -> list[Product]:
    updated_html = click_button_more(browser)
    soup = BeautifulSoup(updated_html, "html.parser")
    products = soup.select(".thumbnail")

    return [
        Product(
            title=product.select_one(".title")["title"].strip(),
            description=product.select_one(".description").text,
            price=float(
                product.select_one("div.caption > h4").text.replace("$", "")
            ),
            rating=len(product.select("div.ratings > p > span")),
            num_of_reviews=int(
                product.select_one("div.ratings > p.pull-right").text.split(
                    " "
                )[0]
            ),
        )
        for product in products
    ]


def get_all_products() -> None:
    url = HOME_URL
    browser = Driver()
    browser.driver.get(url)
    subcategory = subcategory_buttons(browser)
    categories = side_bar_buttons(browser)
    for link in categories:
        name_category = link.split("/")[-1]
        if name_category == "more":
            name_category = "home"
        browser.driver.get(link)
        parse_results = parse_all_products(browser)
        write_file_csv(name_category, parse_results)

    for link in subcategory:
        name_subcategory = link.split("/")[-1]
        browser.driver.get(link)
        parse_results = parse_all_products(browser)
        write_file_csv(name_subcategory, parse_results)


def write_file_csv(name: str, parse_results: list[Product]) -> None:
    with open(f"{name}.csv", "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(PRODUCT_FIELDS)
        for parse in parse_results:
            description = parse.description.replace("\xa0", " ")
            writer.writerow(
                [
                    parse.title,
                    description,
                    parse.price,
                    parse.rating,
                    parse.num_of_reviews,
                ]
            )


if __name__ == "__main__":
    get_all_products()
