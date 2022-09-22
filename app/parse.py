import csv
from dataclasses import dataclass, fields, astuple
from pprint import pprint
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common import ElementNotInteractableException
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service


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
    _instance = None

    def __new__(cls):
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance


def parse_single_product(product_soup) -> Product:
    rating_soup = product_soup.select_one("p[data-rating]")
    if rating_soup:
        rating = (product_soup.select_one("p[data-rating]")["data-rating"])
    else:
        rating = 5
    return Product(
        title=product_soup.select_one(".title")["title"],
        description=product_soup.select_one(".description").text,
        price=float(product_soup.select_one(".price").text.replace("$", "")),
        rating=rating,
        num_of_reviews=int(
            product_soup.select_one(".ratings > .pull-right").text.split()[0]
        )
    )


PRODUCT_FIELDS = [
    field.name
    for field in fields(Product)
]


def get_single_page_products(soup: BeautifulSoup) -> [Product]:
    scroll_more_button = soup.select_one(".ecomerce-items-scroll-more")
    if scroll_more_button is not None:
        driver = WebDriver().driver
        driver.maximize_window()
        url = soup.find("link", {"rel": "canonical"})["href"]
        driver.get(url)
        try:
            while True:
                button = driver.find_element(
                    By.CLASS_NAME, "ecomerce-items-scroll-more"
                )
                ActionChains(driver).move_to_element(button)\
                    .click(button).perform()
        except ElementNotInteractableException:
            print("Stop scrolling")

        elements = driver.find_elements(By.CLASS_NAME, "thumbnail")
        products = []

        for element in elements:
            element_html = element.get_attribute("outerHTML")
            soup = BeautifulSoup(element_html, "html.parser")
            products.append(parse_single_product(soup))
        return products
    else:
        products_soup = soup.select(".thumbnail")
        return [
            parse_single_product(product)
            for product in products_soup
        ]


def get_links(soup) -> dict[str, str]:
    return {
        link.text.strip(): urljoin(BASE_URL, link.get("href"))
        for link in soup
    }


def parse_products() -> dict[str, list[Product]]:
    home_page = requests.get(HOME_URL).content

    home_soup = BeautifulSoup(home_page, "html.parser")

    category_links = get_links(home_soup.select(".category-link"))

    products = {"home": get_single_page_products(home_soup)}

    for name, link in category_links.items():
        page = requests.get(link).content
        soup = BeautifulSoup(page, "html.parser")
        products[name] = get_single_page_products(soup)
        subcategory_links = soup.select(".subcategory-link")
        if subcategory_links:
            links = get_links(subcategory_links)
            for subcategory_name, subcategory_link in links.items():
                subcategory_page = requests.get(subcategory_link).content
                subcategory_soup = BeautifulSoup(
                    subcategory_page, "html.parser"
                )
                products[subcategory_name] = get_single_page_products(
                    subcategory_soup
                )

    return products


def write_products_to_csv(products: dict[str, list[Product]]) -> None:
    for key, value in products.items():
        with open(
                f"{key.lower()}.csv", "w", encoding="UTF8", newline=""
        ) as file:
            writer = csv.writer(file)
            writer.writerow(PRODUCT_FIELDS)
            writer.writerows([astuple(product) for product in value])


def get_all_products():
    with webdriver.Chrome(service=Service(ChromeDriverManager().install())) as driver:
        WebDriver().driver = driver
        products = parse_products()
        pprint(products)
        write_products_to_csv(products)


if __name__ == "__main__":
    get_all_products()
