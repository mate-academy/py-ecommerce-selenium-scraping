from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup, Tag
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait

from app.models import Product
from app.writer import write_products_to_csv

BASE_URL = "https://webscraper.io/"

PAGES = {
    "home.csv": urljoin(BASE_URL, "test-sites/e-commerce/more/"),
    "computers.csv": urljoin(BASE_URL, "test-sites/e-commerce/more/computers"),
    "phones.csv": urljoin(BASE_URL, "test-sites/e-commerce/more/phones"),
    "touch.csv": urljoin(BASE_URL, "test-sites/e-commerce/more/phones/touch"),
    "laptops.csv": urljoin(BASE_URL, "test-sites/e-commerce/more/computers/laptops"),
    "tablets.csv": urljoin(BASE_URL, "test-sites/e-commerce/more/computers/tablets")
}


def get_page_soup(html: bytes | str) -> BeautifulSoup:
    soup = BeautifulSoup(html, "html.parser")
    return soup


def get_single_product(product: Tag) -> Product:
    title = product.select_one("a.title")["title"]
    description = product.select_one("p.description").text.replace("\xa0", " ")
    price = product.select_one("h4.price.float-end").text.replace("$", "")

    rating = len(product.select("div.ratings span"))

    num_of_reviews = product.select_one(
        "p.review-count.float-end"
    ).text.split()[0]

    return Product(
        title=title,
        description=str(description),
        price=float(price),
        rating=rating,
        num_of_reviews=int(num_of_reviews),
    )


def click_btn(driver: webdriver, btn_text: str) -> None:
    link = WebDriverWait(driver, 2).until(
        ec.element_to_be_clickable(
            (By.XPATH, f"//a[contains(text(), '{btn_text}')]")
        )
    )
    driver.execute_script("arguments[0].scrollIntoView(true);", link)
    action = ActionChains(driver)
    action.move_to_element(link).click().perform()


def get_soup_from_paginated_page(url: str) -> BeautifulSoup:
    with webdriver.Chrome() as driver:
        driver.get(url)

        click_btn(driver=driver, btn_text="Accept & Continue")

        while True:
            try:
                click_btn(driver=driver, btn_text="More")
            except TimeoutException:
                break

        soup = get_page_soup(driver.page_source)

        return soup


def parse_single_page(file_name: str, url: str) -> None:
    response = requests.get(url).content
    page_soup = get_page_soup(response)

    more_btn = page_soup.select_one(
        "a.btn.btn-lg.btn-block.btn-primary"
    )

    if more_btn:
        page_soup = get_soup_from_paginated_page(url=url)

    product_blocks = page_soup.select("div.col-md-4.col-xl-4.col-lg-4")
    products = [get_single_product(block) for block in product_blocks]

    write_products_to_csv(output_csv_path=file_name, products=products)


def get_all_products() -> None:
    for file_name, url in PAGES.items():
        parse_single_page(file_name=file_name, url=url)


if __name__ == "__main__":
    get_all_products()
