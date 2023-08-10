import csv
import logging
import time
from dataclasses import dataclass, fields, astuple
from urllib.parse import urljoin

from bs4 import BeautifulSoup, Tag
from selenium import webdriver
from selenium.common import NoSuchElementException
from selenium.webdriver.common.by import By

HOME_URL = "https://webscraper.io/test-sites/e-commerce/more/"

urls = dict(
    HOME_URL=HOME_URL,
    PHONES_URL=urljoin(HOME_URL, "phones"),
    TOUCH_URL=urljoin(HOME_URL, "phones/touch"),
    COMPUTERS_URL=urljoin(HOME_URL, "computers"),
    TABLETS_URL=urljoin(HOME_URL, "computers/tablets"),
    LAPTOPS_URL=urljoin(HOME_URL, "computers/laptops")
)

logging.basicConfig(
    level=logging.INFO
)


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


variable_names = [field.name for field in fields(Product)]


def convert_to_product_instance(product: Tag):
    return Product(
        title=product.select_one(".title")["title"],
        description=product.select_one(".description").text.replace("\xa0", " "),
        price=float(product.select_one(".price").text.replace("$", "")),
        rating=len(product.select(".ws-icon-star")),
        num_of_reviews=int(product.select_one(".ratings > .pull-right").text.split()[0])
    )


def parse_one_page(soup: BeautifulSoup):
    return [convert_to_product_instance(product) for product in soup.select(".thumbnail")]


def click_more_button_if_possible(url: str) -> BeautifulSoup:
    driver = webdriver.Chrome()
    driver.get(url)
    try:
        button = driver.find_element(By.CLASS_NAME, "ecomerce-items-scroll-more")
        while not button.get_attribute("style"):
            driver.execute_script("arguments[0].scrollIntoView();", button)
            button.click()
            time.sleep(.2)
    except NoSuchElementException:
        logging.info("No `more` button on the page")
    finally:
        soup = BeautifulSoup(driver.page_source, "html.parser")
        driver.quit()

    return soup


def write_data_to_csv(data: list[Product], url_name: str):
    with open(
            f"{url_name.split('_')[0].lower()}.csv", mode="w", newline=""
    ) as file:
        writer = csv.writer(file)
        writer.writerow(variable_names)
        writer.writerows([astuple(product) for product in data])
        logging.info(f"Data were parsed!\n")


def get_all_products() -> None:
    for url_name, url in urls.items():
        logging.info(f"Parsing {url_name}")
        write_data_to_csv(parse_one_page(click_more_button_if_possible(url)), url_name=url_name)


if __name__ == "__main__":
    get_all_products()
