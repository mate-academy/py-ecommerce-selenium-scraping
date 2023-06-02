import csv
from dataclasses import astuple, dataclass, fields

from selenium import webdriver
from selenium.common import NoSuchElementException
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement

BASE_URL = "https://webscraper.io/"
HOME_URL = BASE_URL + "test-sites/e-commerce/more/"
COMPUTERS_URL = BASE_URL + "test-sites/e-commerce/more/computers"
LAPTOP_URL = BASE_URL + "test-sites/e-commerce/more/computers/laptops"
TABLETS_URL = BASE_URL + "test-sites/e-commerce/more/computers/tablets"
PHONES_URL = BASE_URL + "test-sites/e-commerce/more/phones"
TOUCH_URL = BASE_URL + "test-sites/e-commerce/more/phones/touch"

URL_FILE_MAP = {
    HOME_URL: "home.csv",
    COMPUTERS_URL: "computers.csv",
    LAPTOP_URL: "laptops.csv",
    TABLETS_URL: "tablets.csv",
    PHONES_URL: "phones.csv",
    TOUCH_URL: "touch.csv",
}


class Driver(object):
    def __init__(self, driver: WebDriver) -> None:
        self.driver = driver


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


PRODUCTS_FIELD = [field.name for field in fields(Product)]


def parse_single_product(product: WebElement) -> Product:
    title = product.find_element(By.CSS_SELECTOR, ".title").get_attribute(
        "title"
    )
    description = product.find_element(By.CSS_SELECTOR, ".description").text
    price = float(
        product.find_element(
            By.CSS_SELECTOR, "div.caption > h4.pull-right.price"
        ).text.replace("$", "")
    )
    ratings_div = product.find_element(By.CSS_SELECTOR, "div.ratings")
    p_element = ratings_div.find_elements(By.TAG_NAME, "p")[1]
    rating = len(p_element.find_elements(By.TAG_NAME, "span"))
    num_of_reviews = int(
        product.find_element(
            By.CSS_SELECTOR, ".ratings > p.pull-right"
        ).text.split()[0]
    )

    return Product(
        title=title,
        description=description,
        price=price,
        rating=rating,
        num_of_reviews=num_of_reviews,
    )


def write_products_to_csv(products_list: [Product], file_name: str) -> None:
    with open(file_name, "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(PRODUCTS_FIELD)
        writer.writerows([astuple(product) for product in products_list])


def click_accept_cookies(driver: WebDriver) -> None:
    try:
        driver.find_element(By.CLASS_NAME, "acceptCookies").click()
    except NoSuchElementException:
        pass


def click_more_button(driver: WebDriver) -> None:
    while True:
        try:
            more_button = driver.find_element(By.LINK_TEXT, "More")
            driver.execute_script("arguments[0].click();", more_button)
        except NoSuchElementException:
            break


def get_all_products() -> None:
    with webdriver.Chrome() as driver:
        driver_instance = Driver(driver)

        for url, file_name in URL_FILE_MAP.items():
            driver_instance.driver.get(url)

            click_accept_cookies(driver_instance.driver)

            click_more_button(driver_instance.driver)

            products = driver_instance.driver.find_elements(
                By.CSS_SELECTOR, ".thumbnail"
            )
            products_list = [
                parse_single_product(product) for product in products
            ]

            write_products_to_csv(products_list, file_name)
