import csv
from dataclasses import dataclass
from typing import List
from urllib.parse import urljoin

from selenium import webdriver
from selenium.common import (
    NoSuchElementException,
    ElementNotInteractableException,
    ElementClickInterceptedException
)
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.webdriver import WebDriver

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


def get_all_pages(driver: WebDriver) -> List[str]:
    links_list = []

    driver.get(HOME_URL)

    main_page_links = driver.find_elements(
        By.CSS_SELECTOR,
        ".sidebar-nav li > a"
    )
    links_list.extend(
        [link.get_attribute("href") for link in main_page_links]
    )

    for link in links_list[1:]:
        driver.get(link)
        nested_page_links = driver.find_elements(
            By.CSS_SELECTOR,
            ".nav-second-level li > a")
        links_list.extend(
            [link_.get_attribute("href") for link_ in nested_page_links]
        )

    return links_list


def get_all_products_on_page(
        link: str,
        driver: WebDriver
) -> List[Product]:
    driver.get(link)
    while True:
        try:
            more_button = driver.find_element(
                By.CLASS_NAME,
                "btn-primary"
            )
            more_button.click()
        except (
                NoSuchElementException,
                ElementClickInterceptedException,
                ElementNotInteractableException
        ):
            break

    product_list_data = []
    product_data = driver.find_elements(By.CLASS_NAME, "thumbnail")
    for product in product_data:
        price = product.find_element(By.CLASS_NAME, "price")
        title = product.find_element(By.CLASS_NAME, "title")
        description = product.find_element(By.CLASS_NAME, "description")
        num_of_reviews = product.find_element(By.CLASS_NAME, "ratings")
        rating = product.find_elements(By.CSS_SELECTOR, "span")

        product_list_data.append(
            Product(
                title=title.get_attribute("title"),
                description=description.text,
                price=float(price.text.replace("$", "")),
                rating=len(rating),
                num_of_reviews=int(num_of_reviews.text.split()[0])
            ))

    return product_list_data


def accept_cookies(driver: WebDriver) -> None:
    driver.get(HOME_URL)
    try:
        cookie_button = driver.find_element(By.CLASS_NAME, "acceptCookies")
        cookie_button.click()
    except NoSuchElementException:
        print("Button 'Accept Cookies' does not exist!")


def write_to_csv_file(
        file_name: str,
        products_list_to_save: List[Product]
) -> None:
    file_path = file_name + ".csv"
    with open(
            file_path, "w", newline="", encoding="utf-8"
    ) as file_to_write:
        fieldnames = [
            "title",
            "description",
            "price",
            "rating",
            "num_of_reviews"
        ]
        writer = csv.DictWriter(
            file_to_write,
            fieldnames=fieldnames
        )
        writer.writeheader()
        for product in products_list_to_save:
            writer.writerow(
                {
                    "title": product.title,
                    "description": product.description,
                    "price": product.price,
                    "rating": product.rating,
                    "num_of_reviews": product.num_of_reviews,
                }
            )


def get_all_products() -> None:
    driver = webdriver.Chrome()
    accept_cookies(driver)

    links_list = get_all_pages(driver=driver)

    for link in links_list:
        products = get_all_products_on_page(link=link, driver=driver)

        file_name = link.split("/")[-1]
        if file_name == "more":
            file_name = "home"

        write_to_csv_file(
            file_name=file_name,
            products_list_to_save=products
        )

    driver.close()


if __name__ == "__main__":
    get_all_products()
