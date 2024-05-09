from dataclasses import dataclass, astuple, fields
from urllib.parse import urljoin
from selenium import webdriver
import csv

from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")
COMPUTERS_URL = urljoin(BASE_URL,
                        "/test-sites/e-commerce/more/computers/")
LAPTOPS_URL = urljoin(BASE_URL,
                      "/test-sites/e-commerce/more/computers/laptops")
PHONES_URL = urljoin(BASE_URL,
                     "test-sites/e-commerce/more/phones")
TABLETS_URL = urljoin(BASE_URL,
                      "/test-sites/e-commerce/more/computers/tablets")
TOUCH_URL = urljoin(BASE_URL, "/test-sites/e-commerce/more/phones/touch")


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


class Driver:
    _driver = None

    @classmethod
    def set_driver(cls, driver: WebDriver) -> None:
        cls._driver = driver

    @classmethod
    def get_driver(cls) -> WebDriver:
        return cls._driver


def write_data_to_csv(products: [WebDriver], file_name: str) -> None:
    with open(file_name, "w", newline="") as f:
        csv_writer = csv.writer(f)
        csv_writer.writerow([field.name for field in fields(Product)])
        csv_writer.writerows([astuple(product) for product in products])


def get_all_products_single_page_driver(url: str) -> [Product]:
    driver = Driver.get_driver()
    driver.get(url)
    if len(driver.find_elements(By.CLASS_NAME,
                                "ecomerce-items-scroll-more")) == 1:
        while True:
            button = driver.find_element(By.CLASS_NAME,
                                         "ecomerce-items-scroll-more")
            if driver.find_element(
                    By.CLASS_NAME,
                    "ecomerce-items-scroll-more").get_attribute("style") != "":
                break
            button.click()

    products = driver.find_elements(By.CLASS_NAME, "product-wrapper")
    response = [
        Product(
            title=product.find_element(By.CLASS_NAME,
                                       "title").get_attribute("title"),
            description=product.find_element(By.CLASS_NAME,
                                             "description").text,
            price=float(product.find_element(By.CLASS_NAME,
                                             "price").text.replace("$", "")),
            rating=len(product.find_element(By.CLASS_NAME,
                                            "ratings").find_elements(
                By.CLASS_NAME, "ws-icon-star")),
            num_of_reviews=int(product.find_element(
                By.CLASS_NAME, "review-count").text.split(" ")[0])
        )
        for product in products
    ]
    return response


def get_laptops() -> None:
    products = get_all_products_single_page_driver(LAPTOPS_URL)
    write_data_to_csv(products, "laptops.csv")


def get_computers() -> None:
    products = get_all_products_single_page_driver(COMPUTERS_URL)

    write_data_to_csv(products, "computers.csv")


def get_phones() -> None:
    products = get_all_products_single_page_driver(PHONES_URL)
    write_data_to_csv(products, "phones.csv")


def get_home_page() -> None:
    products = get_all_products_single_page_driver(HOME_URL)

    write_data_to_csv(products, "home.csv")


def get_tablets() -> None:
    products = get_all_products_single_page_driver(TABLETS_URL)

    write_data_to_csv(products, "tablets.csv")


def get_touches() -> None:
    products = get_all_products_single_page_driver(TOUCH_URL)

    write_data_to_csv(products, "touch.csv")


def get_all_products() -> None:
    with webdriver.Chrome() as driver:
        driver.maximize_window()
        Driver.set_driver(driver)
        get_laptops()
        get_phones()
        get_touches()
        get_tablets()
        get_computers()
        get_home_page()


if __name__ == "__main__":
    get_all_products()
