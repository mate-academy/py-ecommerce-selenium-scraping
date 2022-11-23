import csv
from dataclasses import dataclass
from os.path import exists
from urllib.parse import urljoin

import selenium.webdriver.remote.webelement
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium import webdriver

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int

    def __iter__(self) -> iter:
        return iter([self.title,
                     self.description,
                     self.price,
                     self.rating,
                     self.num_of_reviews])


class SeleniumDriver:

    def __init__(self) -> None:
        self._driver = webdriver.Chrome()

    def get_driver(self) -> selenium.webdriver:
        return self._driver


BROWSER = SeleniumDriver()


def parse_single_product(product_card: WebElement) -> Product:
    name = product_card.find_element(
        By.CLASS_NAME,
        "title"
    ).get_attribute("title")
    descr = product_card.find_element(By.CLASS_NAME, "description").text
    price = float(product_card.find_element(By.CLASS_NAME, "price").text[1:])
    rating_views = product_card.find_element(By.CLASS_NAME, "ratings")
    views = rating_views.find_elements(By.CSS_SELECTOR, "p")
    rating = len(views[-1].find_elements(By.CSS_SELECTOR, "span"))
    num_views = int(views[0].text.split()[0])
    return Product(title=name,
                   description=descr,
                   price=price,
                   rating=rating,
                   num_of_reviews=num_views
                   )


def parsing_page(url: str, file_name: str) -> None:
    driver = BROWSER.get_driver()
    driver.get(url)
    buttons = driver.find_elements(
        By.CLASS_NAME,
        "ecomerce-items-scroll-more"
    )
    if len(buttons) > 0:
        button = buttons[0]
        while button.is_displayed():
            ActionChains(driver).click(button).perform()
            button = driver.find_element(
                By.CLASS_NAME,
                "ecomerce-items-scroll-more"
            )
    product_cards = driver.find_elements(
        By.CLASS_NAME,
        "thumbnail"
    )
    products = []
    for product_card in product_cards:
        products.append(parse_single_product(product_card))
    save_to_file(file_name, products)


def get_all_products() -> None:
    parsing_page(
        "https://webscraper.io/test-sites/e-commerce/more",
        "home.csv"
    )
    parsing_page(
        "https://webscraper.io/test-sites/e-commerce/more/computers",
        "computers.csv"
    )
    parsing_page(
        "https://webscraper.io/test-sites/e-commerce/more/computers/laptops",
        "laptops.csv"
    )
    parsing_page(
        "https://webscraper.io/test-sites/e-commerce/more/computers/tablets",
        "tablets.csv"
    )
    parsing_page(
        "https://webscraper.io/test-sites/e-commerce/more/phones",
        "phones.csv"
    )
    parsing_page(
        "https://webscraper.io/test-sites/e-commerce/more/phones/touch",
        "touch.csv"
    )


def save_to_file(file_name: str, products_list: list[Product]) -> None:
    mode = "w" if exists(file_name) else "x"
    with open(file_name, mode, 100, "utf-8", newline="") as file_to_save:
        fieldnames = ["title",
                      "description",
                      "price",
                      "rating",
                      "num_of_reviews"
                      ]
        writer = csv.writer(file_to_save)
        writer.writerow(fieldnames)
        writer.writerows(products_list)


if __name__ == "__main__":
    get_all_products()
