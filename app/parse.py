import csv
import re
import time
from dataclasses import dataclass
from selenium.webdriver.support import expected_conditions as EC
from typing import List
from urllib.parse import urljoin
from selenium import webdriver
from selenium.common import NoSuchElementException, ElementClickInterceptedException, ElementNotInteractableException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more")

url_lst = [
    HOME_URL,
    HOME_URL + "/phones",
    HOME_URL + "/phones/touch",
    HOME_URL + "/computers",
    HOME_URL + "/computers/tablets",
    HOME_URL + "/computers/laptops",
]


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


def click_more_button(driver) -> None:
    try:
        more_button = driver.find_elements(By.CLASS_NAME, "ecomerce-items-scroll-more")
        if more_button:
            more_button = more_button[0]
            style = more_button.get_attribute("style")

            while not style:
                more_button.click()

                (WebDriverWait(driver, 1).
                 until(EC.presence_of_element_located(
                    (By.CLASS_NAME, "ecomerce-items-scroll-more"))))

                style = more_button.get_attribute("style")

    except ElementClickInterceptedException:
        pass
    except ElementNotInteractableException:
        pass


def get_products(driver) -> List[Product]:
    product_cards = driver.find_elements(By.CLASS_NAME, "thumbnail")
    products = []

    for product_card in product_cards:
        title = product_card.find_element(By.CLASS_NAME, "title").get_attribute("title"),
        description = product_card.find_element(By.CLASS_NAME, "card-text.description").text,
        rating = len(product_card.find_elements(By.CLASS_NAME, "ws-icon.ws-icon-star")),
        num_of_reviews = int(
            re.sub(r"[^0-9]", "", product_card.find_element(By.CLASS_NAME, "ratings").text)
        ),
        price = float(
            product_card.find_element(By.CLASS_NAME, "float-end.price.pull-right").text.replace(
                "$", ""
            )
        ),

        product = Product(
            title=title[0],
            description=description[0],
            rating=rating[0],
            num_of_reviews=num_of_reviews[0],
            price=price[0]
        )
        products.append(product)

    return products


def accept_cookies(driver) -> None:
    try:
        accept_button = driver.find_element(By.CLASS_NAME, "acceptCookies")
        time.sleep(3)
        accept_button.click()
    except NoSuchElementException:
        pass


def create_and_write_to_csv_file(url, products):
    category = url.split("/")[-1]
    csv_file_path = f"{category}.csv"

    with open(csv_file_path, 'w', newline='', encoding='utf-8') as csv_file:
        csv_writer = csv.writer(csv_file)
        for product in products:

            csv_writer.writerow(
                [
                    product.title,
                    product.description,
                    product.price,
                    product.rating,
                    product.num_of_reviews
                ]
            )


def get_all_products() -> None:
    driver = webdriver.Chrome()

    for url in url_lst:
        driver.get(url)
        accept_cookies(driver)
        click_more_button(driver)
        products = get_products(driver)
        create_and_write_to_csv_file(url, products)


if __name__ == "__main__":
    get_all_products()
