import csv
import time
from colorama import Fore, init
from dataclasses import dataclass, astuple, fields
from urllib.parse import urljoin
from selenium import webdriver
from selenium.common import (
    NoSuchElementException,
    ElementClickInterceptedException,
    TimeoutException
)
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from tqdm import tqdm
from webdriver_manager.chrome import ChromeDriverManager


init(autoreset=True)


BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more")
COMPUTERS = urljoin(BASE_URL, "test-sites/e-commerce/more/computers")
LAPTOPS = urljoin(BASE_URL, "test-sites/e-commerce/more/computers/laptops")
TABLETS = urljoin(BASE_URL, "test-sites/e-commerce/more/computers/tablets")
PHONES = urljoin(BASE_URL, "test-sites/e-commerce/more/phones")
TOUCH = urljoin(BASE_URL, "test-sites/e-commerce/more/phones/touch")
ALL_PAGES = [HOME_URL, COMPUTERS, LAPTOPS, TABLETS, PHONES, TOUCH]


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


PRODUCT_FIELDS = [field.name for field in fields(Product)]


_driver: WebDriver


def get_driver() -> WebDriver:
    if _driver is None:
        raise ValueError(
            "WebDriver has not been installed. "
            "Use set_driver() for initialization."
        )
    return _driver


def set_driver(new_driver: WebDriver) -> None:
    global _driver
    _driver = new_driver


def check_more_button(driver: WebDriver) -> None:
    try:
        wait = WebDriverWait(driver, 1)
        button = wait.until(
            ec.presence_of_element_located((By.CLASS_NAME,
                                            "ecomerce-items-scroll-more")))
        while button.is_displayed():
            try:
                button = wait.until(
                    ec.element_to_be_clickable((By.CLASS_NAME,
                                                "ecomerce-items-scroll-more")))
                button.click()
                time.sleep(0.5)
            except ElementClickInterceptedException:
                pass
    except TimeoutException:
        pass
    except NoSuchElementException:
        pass


def check_cookies(driver: WebDriver) -> None:
    try:
        button = driver.find_element(By.CLASS_NAME, "acceptCookies")
        while button.is_displayed():
            button.click()
            time.sleep(0.5)
    except NoSuchElementException:
        pass


def parse_single_product(driver: WebDriver) -> Product:

    return Product(
        title=driver.find_element(By.CLASS_NAME, "title").
        get_attribute("title"),
        description=driver.find_element(By.CLASS_NAME, "description").text,
        price=float(driver.find_element(By.CLASS_NAME, "price").
                    text.replace("$", "")),
        rating=len((driver.find_element(By.CLASS_NAME, "ratings")).
                   find_elements(By.TAG_NAME, "span")),
        num_of_reviews=int(
            driver.find_element(By.CLASS_NAME, "review-count").
            text.split()[0])
    )


def write_products_to_csv(products: [Product], absolute_url: str) -> None:
    filename = absolute_url.split("/")[-1]
    if filename == "more":
        filename = "home"
    full_filename = filename + ".csv"
    with open(full_filename, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(PRODUCT_FIELDS)
        writer.writerows([astuple(product) for product in products])


def parse_page_product(absolute_url: str) -> list[Product]:
    driver = get_driver()
    driver.get(absolute_url)
    check_cookies(driver)
    check_more_button(driver)
    drivers = driver.find_elements(By.CLASS_NAME, "card-body")

    return [parse_single_product(driv) for driv in tqdm(drivers)]


def parse_all_pages() -> None:
    for page in tqdm(
            ALL_PAGES,
            desc=f"{Fore.GREEN}Main Progress: ",
            position=0
    ):
        page_result = parse_page_product(page)
        write_products_to_csv(page_result, page)


def get_all_products() -> None:
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")

    service = Service(ChromeDriverManager().install())

    with webdriver.Chrome(service=service, options=options) as driver:
        set_driver(driver)
        parse_all_pages()


if __name__ == "__main__":
    get_all_products()
