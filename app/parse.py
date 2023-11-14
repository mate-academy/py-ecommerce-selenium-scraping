import csv
from dataclasses import dataclass, fields, astuple
from urllib.parse import urljoin

from selenium.common import (
    NoSuchElementException,
    ElementClickInterceptedException,
    ElementNotInteractableException,
)
from selenium.webdriver import Chrome
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.webdriver import WebDriver

from selenium.webdriver.common.by import By


BASE_URL = "https://webscraper.io/"
PRODUCTS_URLS = {
    "home": (urljoin(BASE_URL, "test-sites/e-commerce/more/"), None),
    "computers": (
        urljoin(BASE_URL, "test-sites/e-commerce/more/computers/"),
        None,
    ),
    "phones": (urljoin(BASE_URL, "test-sites/e-commerce/more/phones/"), None),
    "touch": (
        urljoin(BASE_URL, "test-sites/e-commerce/more/phones/touch"),
        "pagination",
    ),
    "tablets": (
        urljoin(BASE_URL, "test-sites/e-commerce/more/computers/tablets"),
        "pagination",
    ),
    "laptops": (
        urljoin(BASE_URL, "test-sites/e-commerce/more/computers/laptops"),
        "pagination",
    ),
}


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


PRODUCT_FIELDS = [field.name for field in fields(Product)]


class WebDriverSingleton:
    _instance = None

    def __new__(cls, *args, **kwargs) -> WebDriver:
        if not cls._instance:
            cls._instance = super(WebDriverSingleton, cls).__new__(cls)
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            cls._instance.driver = Chrome(options=chrome_options)

        return cls._instance

    @staticmethod
    def get_driver() -> WebDriver:
        return WebDriverSingleton()._instance.driver

    @staticmethod
    def close_driver() -> None:
        driver = WebDriverSingleton()._instance.driver
        if driver:
            driver.quit()
            WebDriverSingleton()._instance.driver = None


def accept_cookies(driver: WebDriver) -> None:
    try:
        accept_cookies_button = driver.find_element(
            By.CLASS_NAME, "acceptCookies"
        )
        accept_cookies_button.click()
    except NoSuchElementException:
        pass


def load_more_products(driver: WebDriver) -> None:
    button = driver.find_element(By.CLASS_NAME, "ecomerce-items-scroll-more")
    while "display: none;" not in button.get_attribute("style"):
        try:
            button.click()
        except ElementClickInterceptedException:
            pass
        except ElementNotInteractableException:
            pass


def parse_single_product(driver: WebDriver) -> Product:
    return Product(
        title=driver.find_element(By.CSS_SELECTOR, ".title").get_attribute(
            "title"
        ),
        description=driver.find_element(By.CSS_SELECTOR, ".description").text,
        price=float(
            driver.find_element(By.CSS_SELECTOR, ".price").text.replace(
                "$", ""
            )
        ),
        rating=int(
            len(driver.find_elements(By.CSS_SELECTOR, ".ws-icon-star"))
        ),
        num_of_reviews=int(
            driver.find_element(By.CSS_SELECTOR, ".review-count").text.split()[
                0
            ]
        ),
    )


def get_single_page_products(driver: WebDriver) -> [Product]:
    products = driver.find_elements(By.CSS_SELECTOR, ".thumbnail")

    return [parse_single_product(product) for product in products]


def write_products_to_csv(products: [Product], csv_path: str) -> None:
    with open(csv_path, "w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(PRODUCT_FIELDS)
        writer.writerows([astuple(product) for product in products])


def get_all_products() -> None:
    driver = WebDriverSingleton().get_driver()

    for name, url in PRODUCTS_URLS.items():
        driver.get(url[0])
        accept_cookies(driver)
        if url[1] == "pagination":
            load_more_products(driver)
        products = get_single_page_products(driver)
        write_products_to_csv(products, f"{name}.csv")
        print(f"Parsed {name}")

    WebDriverSingleton().close_driver()


if __name__ == "__main__":
    get_all_products()
