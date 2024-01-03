import csv
from dataclasses import dataclass
from urllib.parse import urljoin

from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement


BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")
PAGES = {
    "home": "",
    "computers": "computers",
    "laptops": "computers/laptops",
    "tablets": "computers/tablets",
    "phones": "phones",
    "touch": "phones/touch",
}


class ChromeDriver:
    _instance = None

    def __new__(cls) -> "ChromeDriver":
        if not cls._instance:
            cls._instance = super(ChromeDriver, cls).__new__(cls)
            cls._instance.web_driver = webdriver.Chrome()
        return cls._instance

    def __enter__(self) -> "ChromeDriver":
        return self._instance.web_driver

    def __exit__(self,
                 exc_type: type,
                 exc_val: Exception,
                 exc_tb: type) -> None:
        self._instance.web_driver.close()


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


def parse_product(product_element: WebElement) -> Product:
    title = product_element.find_element(
        By.CLASS_NAME, "title"
    ).get_attribute("title")

    price = float(product_element.find_element(
        By.CLASS_NAME, "pull-right"
    ).text.replace("$", ""))

    description = product_element.find_element(
        By.CLASS_NAME, "description"
    ).text

    rating_element = product_element.find_element(
        By.CLASS_NAME, "ratings"
    )
    views = rating_element.find_elements(
        By.CSS_SELECTOR, "p"
    )
    num_of_reviews = int(views[0].text.split()[0])
    rating = len(views[-1].find_elements(By.CSS_SELECTOR, "span"))

    return Product(
        title=title,
        description=description,
        price=price,
        rating=rating,
        num_of_reviews=num_of_reviews
    )


def save_file(file_name: str, products: list[Product]) -> None:
    with open(file_name, "w") as f:
        fieldnames = [
            "title",
            "description",
            "price",
            "rating",
            "num_of_reviews"
        ]

        csvwriter = csv.writer(f)
        csvwriter.writerow(fieldnames)

        for product in products:
            csvwriter.writerow([
                product.title,
                product.description,
                product.price,
                product.rating,
                product.num_of_reviews
            ])


def load_all_pages(driver: WebDriver) -> None:
    if len(driver.find_elements(
            By.CLASS_NAME, "ecomerce-items-scroll-more"
    )) > 0:
        button = driver.find_element(
            By.CLASS_NAME, "ecomerce-items-scroll-more"
        )
        if button.is_displayed():
            ActionChains(driver).click(button).perform()
            load_all_pages(driver)


def parse_page(url: str, file_name: str, driver: WebDriver) -> None:
    driver.get(url)
    load_all_pages(driver)

    products_card = driver.find_elements(By.CLASS_NAME, "thumbnail")
    products = [parse_product(product) for product in products_card]

    save_file(file_name, products)


def get_all_products() -> None:
    with ChromeDriver() as driver:
        for name, url in PAGES.items():
            print(f"{HOME_URL}{url}", f"{name}.csv")
            parse_page(f"{HOME_URL}{url}", f"{name}.csv", driver)


if __name__ == "__main__":
    get_all_products()
