import csv
from dataclasses import dataclass, fields, astuple
from urllib.parse import urljoin

from tqdm import tqdm
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.common import (
    TimeoutException,
    ElementNotInteractableException,
    ElementClickInterceptedException,
)


BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")
COMPUTERS_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/computers")
LAPTOPS_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/computers/laptops")
TABLETS_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/computers/tablets")
PHONE_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/phones")
TOUCH_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/phones/touch")

PAGES = (
    (HOME_URL, "home.csv"),
    (COMPUTERS_URL, "computers.csv"),
    (LAPTOPS_URL, "laptops.csv"),
    (TABLETS_URL, "tablets.csv"),
    (PHONE_URL, "phones.csv"),
    (TOUCH_URL, "touch.csv"),
)


class WebDriver:

    def __init__(self) -> None:
        self._driver = None

    @property
    def driver(self) -> webdriver.Chrome:
        if not self._driver:
            raise NotImplementedError
        return self._driver

    @driver.setter
    def driver(self, driver: callable(webdriver.Chrome)) -> None:
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        self._driver = driver(options)


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


DRIVER = WebDriver()

PRODUCT_FIELDS = [field.name for field in fields(Product)]


def accept_cookies(driver: WebDriver) -> None:
    try:
        wait = WebDriverWait(driver, 5)
        cookies = wait.until(
            ec.element_to_be_clickable((By.CLASS_NAME, "acceptCookies"))
        )
        cookies.click()
    except TimeoutException:
        pass


def scroll_more(driver: WebDriver) -> None:
    while True:
        try:
            wait = WebDriverWait(driver, 5)
            more = wait.until(
                ec.presence_of_element_located(
                    (By.CLASS_NAME, "ecomerce-items-scroll-more")
                )
            )
            more.click()
        except (
            TimeoutException,
            ElementNotInteractableException,
            ElementClickInterceptedException,
        ):
            break


def parse_single_product(product: WebElement) -> Product | None:
    title = product.find_element(By.CLASS_NAME, "title").get_attribute("title")
    description = product.find_element(By.CLASS_NAME, "description").text
    try:
        price = product.find_element(By.CLASS_NAME, "price").text
        price = float(price.replace("$", ""))
    except Exception as e:
        price = None
    try:
        review_count = product.find_element(By.CLASS_NAME, "review-count").text
        review_count = int(review_count.split(" ")[0])
    except Exception as e:
        review_count = None
    rating = len(product.find_elements(By.CLASS_NAME, "ws-icon-star"))
    return Product(
        title=title,
        description=description,
        price=price,
        rating=rating,
        num_of_reviews=review_count,
    )


def parse_page_products(url: str, pbar: tqdm) -> list[Product]:

    driver = DRIVER.driver
    driver.get(url)

    accept_cookies(driver)
    scroll_more(driver)

    elements = driver.find_elements(By.CLASS_NAME, "product-wrapper")

    result = []
    for element in elements:
        product = parse_single_product(element)
        if product:
            result.append(product)
        pbar.update(1)
    return result


def write_page_to_csv(filename: str, products: list[Product]) -> None:
    with open(filename, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(PRODUCT_FIELDS)
        writer.writerows([astuple(product) for product in products])
    return


def get_all_products(pages: tuple[tuple[str]] = PAGES) -> None:
    try:
        DRIVER.driver = webdriver.Chrome

        all_products = []
        bar_format = (
            "{desc}: {percentage:3.0f}% |{bar}| "
            "{n_fmt}/{total_fmt} • {elapsed}s • {rate_fmt}"
        )
        with tqdm(
            total=156,
            desc="Parsing products",
            unit="products",
            colour="magenta",
            ascii="░▒▓█",
            bar_format=bar_format,
            dynamic_ncols=True,
        ) as pbar:
            for i, page in enumerate(pages):
                url = page[0]
                csv_file_name = page[1]

                pbar.set_description_str(f"Page {i}/{len(pages)}: {url}")
                products = parse_page_products(url, pbar)
                write_page_to_csv(csv_file_name, products)
                all_products.extend(products)
    finally:
        DRIVER.driver.quit()


if __name__ == "__main__":
    get_all_products(PAGES)
