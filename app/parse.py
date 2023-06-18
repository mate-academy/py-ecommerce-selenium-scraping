import csv
import logging
import sys
from dataclasses import dataclass, fields, astuple
from typing import Type
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from tqdm import tqdm

from app.utils import CustomDriver

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")

logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)8s]:   %(message)s",
    handlers=[
        logging.FileHandler("parser.log"),
        logging.StreamHandler(sys.stdout),
    ],
)


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int
    additional_info: dict


def get_page_soup(url: str) -> BeautifulSoup:
    page = requests.get(url).content
    return BeautifulSoup(page, "html.parser")


def parse_hdd(driver: WebDriver) -> dict[str, float]:
    prices = {}
    swatches = driver.find_elements(By.CLASS_NAME, "swatches")
    if swatches:
        buttons = swatches[0].find_elements(By.TAG_NAME, "button")
        for button in buttons:
            if not button.get_property("disabled"):
                button.click()
                prices[button.get_property("value")] = float(
                    driver.find_element(By.CLASS_NAME, "price").text[1:]
                )
    return prices


def parse_color(driver: WebDriver) -> list[str]:
    colors = []
    thumbnails = driver.find_elements(By.CLASS_NAME, "thumbnail")
    if thumbnails:
        dropdown_menus = thumbnails[0].find_elements(By.CLASS_NAME, "dropdown")
        if dropdown_menus:
            options = dropdown_menus[0].find_elements(By.TAG_NAME, "option")
            for option in options:
                value = option.get_attribute("value")
                if value:
                    option.click()
                    colors.append(value)
    return colors


def parse_additional_info(
    product: BeautifulSoup,
) -> dict[str, dict[str, float] | list[str]]:
    additional_info = {}
    detailed_url = urljoin(
        BASE_URL,
        product.select_one("a")["href"],
    )
    my_driver = CustomDriver()
    my_driver.get(detailed_url)

    hdd_prices = parse_hdd(my_driver.driver)
    colors = parse_color(my_driver.driver)

    if hdd_prices:
        additional_info["hdd prices"] = hdd_prices
    if colors:
        additional_info["colors"] = colors
    return additional_info


def parse_product(product: BeautifulSoup) -> Product:
    return Product(
        title=product.select_one(".title")["title"],
        description=product.select_one(".description").text.replace(
            "\xa0", " "
        ),
        price=float(product.select_one(".price").text[1:]),
        rating=len(product.select(".glyphicon-star")),
        num_of_reviews=int(product.select_one(".ratings").text.split()[0]),
        additional_info=parse_additional_info(product),
    )


def parse_page(key: str, link: str) -> list[Product]:
    my_driver = CustomDriver()
    my_driver.get(link)
    my_driver.click_more()
    soup = BeautifulSoup(my_driver.page_source(), "html.parser")
    elements = soup.select(".thumbnail")
    return [
        parse_product(element)
        for element in tqdm(elements, position=0, desc=f"Parse {key: <20}")
    ]


def get_obj_fields(obj: Type[Product]) -> list[str]:
    return [field.name for field in fields(obj)]


def write_obj_to_csv(
    output_csv_path: str,
    all_obj: [Product],
) -> None:
    with open(output_csv_path, "w") as file:
        writer = csv.writer(file)
        writer.writerow(get_obj_fields(Product))
        writer.writerows([astuple(obj) for obj in all_obj])


def menu_links(url: str) -> dict[str, str]:
    links = {}
    menu = get_page_soup(url).select_one(".sidebar")
    a_links = menu.select("a")
    for link in a_links:
        links[link.text.strip()] = urljoin(BASE_URL, link["href"])
        sub_links = {}
        soup = get_page_soup(urljoin(BASE_URL, link["href"]))
        sub_menu = soup.select_one(".nav-second-level")
        if sub_menu:
            sub_links = {
                a.text.strip(): urljoin(BASE_URL, a["href"])
                for a in sub_menu.select("a")
            }
        links.update(sub_links)
    return links


def get_all_products() -> None:
    my_driver = CustomDriver()
    logging.info("Start parsing products")
    dict_links = menu_links(HOME_URL)
    for key, link in tqdm(
        dict_links.items(), position=0, desc="Parsing products"
    ):
        write_obj_to_csv(key + ".csv", parse_page(key, link))
    my_driver.close()


if __name__ == "__main__":
    get_all_products()
