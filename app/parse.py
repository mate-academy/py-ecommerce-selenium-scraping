import dataclasses
import logging
import sys
import time
from dataclasses import dataclass
from typing import Any, List
from urllib.parse import urljoin
from bs4 import Tag, BeautifulSoup
import csv

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as e_cond
from tqdm import tqdm

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")
COMPUTER_URL = urljoin(HOME_URL, "computers/")
LAPTOPS_URL = urljoin(COMPUTER_URL, "laptops")
TABLETS_URL = urljoin(COMPUTER_URL, "tablets")
PHONE_URL = urljoin(HOME_URL, "phones/")
TOUCH_URL = urljoin(PHONE_URL, "touch")


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


PRODUCTS_FIELDS = [field.name for field in dataclasses.fields(Product)]

logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)8s]: %(message)s",
    handlers=[
        logging.FileHandler("parser.log"),
        logging.StreamHandler(sys.stdout)
    ],
)


class SingletonMeta(type):
    _instances = {}

    def __call__(cls, *args, **kwargs) -> Any:
        if cls not in cls._instances:
            instance = super().__call__(*args, **kwargs)
            cls._instances[cls] = instance
        return cls._instances[cls]


class SeleniumBrowser(metaclass=SingletonMeta):
    def __init__(self) -> None:
        logging.info("Initializing driver")
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        self.driver = webdriver.Chrome(options=chrome_options)

    def get_driver(self) -> webdriver:
        logging.info("Getting driver")
        return self.driver

    def close_driver(self) -> None:
        logging.info("Closing driver")
        self.driver.close()
        del SeleniumBrowser._instances[type(self)]


def parse_single_product(product: Tag) -> Product:
    return Product(
        title=product.select_one("a.title")["title"],
        description=product.select_one(".description")
        .text.replace("\xa0", " "),
        price=float(product.select_one(".price")
                    .text.replace("$", "")),
        rating=int(len(product.select("span.ws-icon-star"))),
        num_of_reviews=int(product.select_one(".review-count")
                           .text.split()[0]),
    )


def get_products(driver: webdriver) -> List[Product]:
    page_soup = BeautifulSoup(driver.page_source, "html.parser")
    products = page_soup.select(".product-wrapper")
    return [parse_single_product(product) for product in products]


def get_products_from_page(url: str) -> List[Product]:
    driver = SeleniumBrowser().get_driver()
    driver.get(url)
    logging.info(f"Getting products from page {url}")
    WebDriverWait(driver, 10)
    cookies_btn = driver.find_elements(By.CSS_SELECTOR, "button.acceptCookies")
    if cookies_btn:
        logging.info("Accepting cookies")
        cookies_btn[0].click()

    more_btn = driver.find_elements(
        By.CSS_SELECTOR, "a.ecomerce-items-scroll-more"
    )
    if more_btn:
        more_btn = more_btn[0]
        more_btn_style = more_btn.get_attribute("style")
        pbar = tqdm()
        while "display: none" not in more_btn_style:
            driver.execute_script("arguments[0].click();", more_btn)
            more_btn = WebDriverWait(driver, 5).until(
                e_cond.presence_of_element_located(
                    (By.CSS_SELECTOR, "a.ecomerce-items-scroll-more")
                )
            )
            more_btn_style = more_btn.get_attribute("style")
            pbar.update(1)
    return get_products(driver)


def save_products_to_csv(products: List[Product], filename: str) -> None:
    """
    Збереження списку продуктів у CSV-файл.
    """
    with open(filename, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(PRODUCTS_FIELDS)
        writer.writerows([dataclasses.astuple(product)
                          for product in products])


def get_all_products() -> None:
    page_urls = [
        HOME_URL, COMPUTER_URL, PHONE_URL, LAPTOPS_URL, TABLETS_URL, TOUCH_URL
    ]
    file_names = [
        "home.csv",
        "computers.csv",
        "phones.csv",
        "laptops.csv",
        "tablets.csv",
        "touch.csv",
    ]
    for filenum, page_url in enumerate(page_urls):
        filename = file_names[filenum]
        save_products_to_csv(
            filename=filename,
            products=get_products_from_page(page_url)
        )
    SeleniumBrowser().close_driver()


if __name__ == "__main__":
    get_all_products()
