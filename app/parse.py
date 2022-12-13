import csv
import time
from dataclasses import dataclass, fields, astuple
from urllib.parse import urljoin
from selenium import webdriver
from selenium.common import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement

BASE_URL = "https://webscraper.io"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")
LIST_URLS = [
    (HOME_URL, "home.csv"),
    (urljoin(HOME_URL, "computers"), "computers.csv"),
    (urljoin(HOME_URL, "computers/laptops"), "laptops.csv"),
    (urljoin(HOME_URL, "computers/tablets"), "tablets.csv"),
    (urljoin(HOME_URL, "phones"), "phones.csv"),
    (urljoin(HOME_URL, "phones/touch"), "touch.csv"),
]


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


PRODUCT_FIELDS = [field.name for field in fields(Product)]

_driver: WebDriver | None = None


class ChromeDriver:
    def __init__(self) -> None:
        self.__driver = webdriver.Chrome()

    @property
    def get_driver(self) -> WebDriver:
        return self.__driver


def parse_single_product(driv: WebElement) -> [Product]:
    return Product(
        title=driv.find_element(
            By.CLASS_NAME, "title").get_attribute("title"),
        description=driv.find_element(
            By.CLASS_NAME, "description").text,
        price=float(driv.find_element(
            By.CLASS_NAME, "pull-right").text.replace("$", "")),
        rating=len(driv.find_element(
            By.CLASS_NAME, "ratings").find_elements(
            By.CLASS_NAME, "glyphicon-star"
        )
        ),
        num_of_reviews=int(driv.find_element(
            By.CSS_SELECTOR, ".ratings .pull-right"
        ).text.split()[0]))


def search_urls(url: str) -> list:
    driver = webdriver.Chrome()
    driver.get(url)
    swathes = driver.find_element(By.ID, "side-menu")
    buttons = swathes.find_elements(By.TAG_NAME, "a")
    links_list = [url]
    for i in buttons[1:]:
        links_list.append(i.get_attribute("href"))
        i.click()
        new_swatches = driver.find_elements(
            By.CSS_SELECTOR, "a.subcategory-link"
        )
        for swatch in new_swatches:
            links_list.append(swatch.get_attribute("href"))
        driver.back()
    return links_list


def get_single_page_product(driv: WebDriver, url: str) -> [Product]:
    driv.get(url)
    try:
        cookies = driv.find_element(By.CLASS_NAME, "acceptCookies")
        if cookies.is_displayed():
            cookies.click()
    except NoSuchElementException:
        pass
    try:
        more_button = driv.find_element(
            By.CLASS_NAME, "ecomerce-items-scroll-more"
        )
    except NoSuchElementException:
        pass
    else:
        while more_button.is_displayed():
            more_button.click()
            time.sleep(0.1)
    finally:
        products = driv.find_elements(By.CLASS_NAME, "thumbnail")
    return [parse_single_product(product) for product in products]


def write_products_to_csv(products: [Product], output_csv_path: str) -> None:
    with open(output_csv_path, "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(PRODUCT_FIELDS)
        writer.writerows([astuple(product) for product in products])


def get_all_products() -> None:
    with webdriver.Chrome() as driver:
        for url in LIST_URLS:
            write_products_to_csv(
                get_single_page_product(driver, url[0]), url[1]
            )


if __name__ == "__main__":
    get_all_products()
