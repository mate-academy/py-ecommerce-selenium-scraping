import csv
from dataclasses import dataclass

from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support import expected_conditions as EC
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait

from configs import DRIVER_PATH, HOME_URL, BASE_URL


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


def get_links(soup: BeautifulSoup, search_by: str = None) -> list[str]:
    if search_by:
        return [
            link.get("href") for link in soup.select(f"a[href*={search_by}]")
        ]
    links = soup.select("a[href]")
    return [link.get("href") for link in links]


def get_soup_object(url: str) -> BeautifulSoup:
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")
    return soup


def create_product(product: BeautifulSoup) -> Product:
    title = product.select_one(".title").get("title")
    description = product.select_one(".description").text
    price = float(product.select_one(".price").text.replace("$", ""))
    rating = len(product.select("div.ratings > span"))
    num_of_reviews = int(
        product.select_one("div.ratings > p.pull-right").text.split()[0]
    )

    new_prod = Product(
        title=title,
        description=description,
        price=price,
        rating=rating,
        num_of_reviews=num_of_reviews,
    )
    print(new_prod.title + " created")
    return new_prod


def parse_page(
        soup: BeautifulSoup, tag: str, selector_type: str, selector_name: str
):
    products = soup.find_all(tag, {selector_type: selector_name})
    return [create_product(product) for product in products]


def write_to_csv(products: list, filename: str):
    with open(filename, mode="w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(
            ["Title", "Description", "Price", "Rating", "Number of Reviews"]
        )
        for product in products:
            writer.writerow(
                [
                    product.title,
                    product.description,
                    product.price,
                    product.rating,
                    product.num_of_reviews,
                ]
            )


def click_button(
        driver: webdriver, button_selector: str, wait_for_selector: str = None
) -> None:
    more_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, button_selector))
    )
    more_button.click()
    if wait_for_selector:
        WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located(
                (By.CSS_SELECTOR, wait_for_selector)
            )
        )


def create_web_driver(driver_path: str) -> webdriver:
    service = Service(driver_path)
    driver = webdriver.Chrome(service=service)
    return driver


def get_all_products() -> None:
    home_page_soup = get_soup_object(HOME_URL)
    home_products = parse_page(
        soup=home_page_soup,
        tag="div",
        selector_type="class",
        selector_name="thumbnail",
    )

    computer_page_link = urljoin(
        HOME_URL, get_links(home_page_soup, search_by="computers")[0]
    )
    computer_page_soup = get_soup_object(computer_page_link)
    comp_sublinks = get_links(computer_page_soup.select_one(".nav-second-level"), )
    computer_products = parse_page(
        soup=computer_page_soup,
        tag="div",
        selector_type="class",
        selector_name="thumbnail",
    )
    write_to_csv(home_products, "home.csv")
    write_to_csv(computer_products, "computer.csv")

    driver = create_web_driver(DRIVER_PATH)
    for link in comp_sublinks:
        url = urljoin(BASE_URL, link)
        driver.get(url)
        try:
            click_button(driver, ".acceptCookies")
        except Exception as err:
            print(err)
        while True:
            try:
                click_button(driver, ".ecomerce-items-scroll-more", "div.thumbnail")
            except:
                break
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, "html.parser")
        products = parse_page(
            soup=soup,
            tag="div",
            selector_type="class",
            selector_name="thumbnail",
        )
        file_name = link.split("/")[-1]
        write_to_csv(products, f"{file_name}.csv")


if __name__ == "__main__":
    get_all_products()
