import csv
from dataclasses import dataclass, astuple
from urllib.parse import urljoin

from selenium import webdriver
from selenium.common import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement

from time import sleep

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")

LIST_URL = {
    "home": HOME_URL,
    "computers": urljoin(HOME_URL, "computers"),
    "laptops": urljoin(HOME_URL, "computers/laptops"),
    "tablets": urljoin(HOME_URL, "computers/tablets"),
    "phones": urljoin(HOME_URL, "phones"),
    "touch": urljoin(HOME_URL, "phones/touch"),

}


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


_driver: WebDriver | None = None


class ChromeDriver:
    def __init__(self) -> None:
        self.__driver = webdriver.Chrome()

    @property
    def get_driver(self) -> WebDriver:
        return self.__driver


def parse_single_product(driver: WebElement) -> Product:
    return Product(
        title=driver.find_element(
            By.CLASS_NAME, "title"
        ).get_attribute("title"),
        description=driver.find_element(
            By.CLASS_NAME, "description"
        ).text,
        price=float(driver.find_element(
            By.CLASS_NAME, "price"
        ).text.replace("$", "")),
        rating=len(driver.find_elements(
            By.CLASS_NAME, "glyphicon-star")),
        num_of_reviews=int(driver.find_element(
            By.CSS_SELECTOR, ".ratings .pull-right"
        ).text.split()[0], )
    )


def save_file(products: [Product], file_name) -> None:
    with open(file_name, "w", newline="") as file:
        rows_titles = [
            "title",
            "description",
            "price",
            "rating",
            "num_of_reviews",
        ]
        csvwriter = csv.writer(file)
        csvwriter.writerow(rows_titles)
        csvwriter.writerows([astuple(product) for product in products])


def accept_cookies(driver: WebDriver) -> None:
    try:
        cookies = driver.find_element(By.CLASS_NAME, "acceptCookies")
        if cookies.is_displayed():
            cookies.click()
    except NoSuchElementException:
        pass


def get_single_page_product(url: str, driver: WebDriver) -> [Product]:
    driver.get(url)
    try:
        more_button = driver.find_element(
            By.CLASS_NAME, "ecomerce-items-scroll-more"
        )
        accept_cookies(driver)
    except NoSuchElementException:
        pass
    else:
        while more_button.is_displayed():
            more_button.click()
            sleep(0.1)
    finally:
        products = driver.find_elements(By.CLASS_NAME, "thumbnail")
        return [parse_single_product(product) for product in products]


def get_all_products() -> None:
    with webdriver.Chrome() as new_driver:
        for file_name, page in LIST_URL.items():
            save_file(get_single_page_product(page, new_driver), file_name + ".csv")


if __name__ == "__main__":
    get_all_products()
