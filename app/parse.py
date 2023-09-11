import csv
from dataclasses import dataclass, astuple
from urllib.parse import urljoin
from selenium import webdriver
from selenium.common import (
    NoSuchElementException,
    ElementClickInterceptedException,
    ElementNotInteractableException
)
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By

BASE_URL = "https://webscraper.io/"
URLs = [
    urljoin(BASE_URL, "test-sites/e-commerce/more"),
    urljoin(BASE_URL, "test-sites/e-commerce/more/computers"),
    urljoin(BASE_URL, "test-sites/e-commerce/more/computers/laptops"),
    urljoin(BASE_URL, "/test-sites/e-commerce/more/computers/tablets"),
    urljoin(BASE_URL, "test-sites/e-commerce/more/phones"),
    urljoin(BASE_URL, "test-sites/e-commerce/more/phones/touch")
]


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


def accept_cookies(driver: WebDriver) -> None:
    driver.get(URLs[0])
    try:
        cookie_button = driver.find_element(By.CLASS_NAME, "acceptCookies")
        cookie_button.click()
    except NoSuchElementException:
        print("Button 'Accept Cookies' does not exist!")


def get_all_products_on_page(url: str, driver: WebDriver) -> list:
    driver.get(url)

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
            print("qqqq")
            break
    products_list = []

    products = driver.find_elements(By.CLASS_NAME, "thumbnail")
    for product in products:
        title = product.find_element(
            By.CLASS_NAME, "title"
        ).get_attribute("title")
        description = product.find_element(
            By.CLASS_NAME, "description"
        ).text
        price = product.find_element(
            By.CLASS_NAME, "price"
        ).text
        rating = product.find_elements(
            By.CSS_SELECTOR, "span"
        )
        num_of_reviews = product.find_element(
            By.CLASS_NAME, "ratings"
        ).text

        products_list.append(
            Product(
                title=title,
                description=description,
                price=float(price[1:]),
                rating=len(rating),
                num_of_reviews=int(num_of_reviews.split()[0]),
            )
        )

    return products_list


def write_to_csv(filename: str, products_list: list[Product]) -> None:
    with open(filename, "w", encoding="UTF-8", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["title",
                         "description",
                         "price",
                         "rating",
                         "num_of_reviews"
                         ])
        for product in products_list:
            writer.writerow(astuple(product))


def get_all_products() -> None:
    driver = webdriver.Chrome()
    accept_cookies(driver)
    for url in URLs:

        products = get_all_products_on_page(url, driver)
        print(products)
        filename = url.split("/")[-1]
        if filename == "more":
            filename = "home"
        filename += ".csv"
        write_to_csv(filename, products)


if __name__ == "__main__":
    get_all_products()
