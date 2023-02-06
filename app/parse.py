import csv
from dataclasses import dataclass, astuple
from urllib.parse import urljoin
from selenium import webdriver
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")
PRODUCT_FIELDS = ["title", "description", "price", "rating", "num_of_reviews"]


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


class WebDriverChrome:
    def __init__(self, driver: None | WebDriver = None) -> None:
        self._driver = driver

    @property
    def driver_chrome(self) -> None | WebDriver:
        return self._driver

    @driver_chrome.setter
    def driver_chrome(self, value: WebDriver) -> None:
        if isinstance(value, WebDriver):
            self._driver = value
        else:
            raise Exception("Driver is invalid")


def parse_single_product(product_soup: WebElement) -> Product:
    count = 0
    for _ in product_soup.find_elements(By.CSS_SELECTOR, ".glyphicon-star"):
        count += 1
    return Product(
        title=product_soup.find_element(By.CLASS_NAME, "title").text,
        description=product_soup.find_element(
            By.CLASS_NAME,
            "description"
        ).text,
        price=float(product_soup.find_element(
            By.CLASS_NAME,
            "price"
        ).text.replace("$", "")),
        rating=count,
        num_of_reviews=int(product_soup.find_element(
            By.CSS_SELECTOR,
            "div.ratings > .pull-right"
        ).text.split()[0]),
    )


def get_page_products(path: str, driver: WebDriver) -> list[Product]:
    url = urljoin(HOME_URL, path)

    driver.get(url)

    try:
        button = driver.find_element(
            By.CLASS_NAME,
            "ecomerce-items-scroll-more"
        )
        if button:
            while button.value_of_css_property("display") != "none":
                button.click()
    except Exception:
        pass

    products = driver.find_elements(By.CLASS_NAME, "thumbnail")

    return [parse_single_product(product) for product in products]


def write_to_csv_file(path: str, products: list[Product]) -> None:
    path_file = {
        "": "home.csv",
        "computers/": "computers.csv",
        "phones/": "phones.csv",
        "computers/laptops": "laptops.csv",
        "phones/touch": "touch.csv",
        "computers/tablets": "tablets.csv",
    }

    for key, file_name in path_file.items():
        if path == key:
            with open(
                    file_name,
                    "w",
                    encoding="utf-8",
                    newline=""
            ) as file_csv:
                writer = csv.writer(file_csv)
                writer.writerow(PRODUCT_FIELDS)
                writer.writerows([astuple(product) for product in products])


def get_all_products() -> None:
    urls = [
        "",
        "computers/",
        "phones/",
        "computers/laptops",
        "phones/touch",
        "computers/tablets"
    ]
    with webdriver.Chrome() as new_driver:
        driver = WebDriverChrome(new_driver)
        driver = driver.driver_chrome
        driver.get(HOME_URL)

        cookies = driver.find_element(By.CLASS_NAME, "acceptCookies")
        cookies.click()
        for path in urls:
            write_to_csv_file(path, get_page_products(path, driver))


if __name__ == "__main__":
    get_all_products()
