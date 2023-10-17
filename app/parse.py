import time
from dataclasses import dataclass
from urllib.parse import urljoin

from dataclass_csv import DataclassWriter
import selenium
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")

URL_MAP = {
    HOME_URL: "home.csv",
    urljoin(HOME_URL, "computers"): "computers.csv",
    urljoin(HOME_URL, "computers/laptops"): "laptops.csv",
    urljoin(HOME_URL, "computers/tablets"): "tablets.csv",
    urljoin(HOME_URL, "phones"): "phones.csv",
    urljoin(HOME_URL, "phones/touch"): "touch.csv",
}


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int

    @classmethod
    def get_product(cls, driver: webdriver) -> 'Product':
        return cls(
            title=driver.find_element(By.CLASS_NAME, "title")
                        .get_attribute("title"),
            description=driver.find_element(By.CLASS_NAME, "description").text,
            price=float(
                driver.find_element(By.CLASS_NAME, "price").text.replace("$", "")
            ),
            rating=int(len(driver.find_elements(By.CLASS_NAME, "glyphicon-star"))),
            num_of_reviews=int(
                driver.find_element(By.CSS_SELECTOR, ".ratings .review-count")
                            .text.split()[0]
            ),
        )


def parse_page(url: str, driver: webdriver) -> [Product]:
    driver.get(url)

    try:
        driver.find_element(By.CLASS_NAME, "acceptCookies").click()
    except selenium.common.exceptions.NoSuchElementException:
        pass

    try:
        while True:
            driver.find_element(
                By.CLASS_NAME, "ecomerce-items-scroll-more").click()
            time.sleep(0.2)
    except (selenium.common.exceptions.NoSuchElementException,
            selenium.common.exceptions.ElementNotInteractableException):
        pass

    products = driver.find_elements(By.CLASS_NAME, "thumbnail")
    return [Product.get_product(product_driver) for product_driver in products]


def write_to_csv(products: list[Product], path: str) -> None:
    with open(path, "w", newline="",) as file:
        writer = DataclassWriter(file, products, Product)
        writer.write()


def get_all_products() -> None:

    with webdriver.Chrome(
            service=Service(ChromeDriverManager().install())) as driver:
        for url, path in URL_MAP.items():
            write_to_csv(
                parse_page(url, driver),
                path
            )


if __name__ == "__main__":
    get_all_products()
