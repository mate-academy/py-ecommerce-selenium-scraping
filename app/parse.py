import csv
from dataclasses import dataclass, fields, astuple
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common import NoSuchElementException
from selenium.webdriver.common.by import By

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more")

pages_dict = {
    "home": "/",
    "computers": "/computers",
    "laptops": "/computers/laptops",
    "tablets": "/computers/tablets",
    "phones": "/phones",
    "touch": "/phones/touch"
}


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


PRODUCT_FIELD = [field.name for field in fields(Product)]


def parse_single_product(product: BeautifulSoup) -> Product:
    return Product(
        title=product.select_one(".title")["title"],
        description=(
            product.select_one(".description").text.replace("\xa0", " ")
        ),
        price=float(product.select_one(".price").text.replace("$", "")),
        rating=int(len(product.select_one("div.ratings").contents[1])),
        num_of_reviews=int(
            product.select_one("div.ratings > p.review-count").text.split()[0]
        )
    )


def get_page_all_products(page_soup: BeautifulSoup) -> [Product]:
    products_on_page = page_soup.select(".card-body")

    return [parse_single_product(product) for product in products_on_page]


def parse_all_products_on_page(url: str) -> [Product]:
    driver = webdriver.Chrome()
    driver.get(url)

    while True:
        try:
            button_more = driver.find_element(
                By.CLASS_NAME, "ecomerce-items-scroll-more"
            )
            tag_style = button_more.get_property("style")

            if len(tag_style) == 1:
                break
            driver.execute_script("arguments[0].click();", button_more)
        except NoSuchElementException:
            break

    soup = BeautifulSoup(driver.page_source, "html.parser")
    return get_page_all_products(soup)


def write_vacancies_to_csv(products: [Product], output_csv_path: str) -> None:
    with open(output_csv_path, "w") as file:
        writer = csv.writer(file)
        writer.writerow(PRODUCT_FIELD)
        writer.writerows([astuple(product) for product in products])


def get_all_products() -> [Product]:
    for name, path in pages_dict.items():
        url = HOME_URL + path

        all_products = parse_all_products_on_page(url)

        name_of_file = name + ".csv"
        write_vacancies_to_csv(
            products=all_products, output_csv_path=name_of_file
        )


if __name__ == "__main__":
    get_all_products()
