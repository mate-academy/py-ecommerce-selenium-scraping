import csv
from dataclasses import dataclass, fields
from urllib.parse import urljoin

from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


PRODUCTS_FIELDS = [field.name for field in fields(Product)]


class ChromeDriver:
    def __init__(self) -> None:
        options = Options()
        options.add_argument("--headless")
        self._driver = webdriver.Chrome(options=options)

    def __enter__(self) -> WebDriver:
        return self._driver

    def __exit__(
            self,
            exception_type: type,
            exception_val: Exception,
            exception_tb: type
    ) -> None:
        self._driver.close()


def extract_product(product_element: WebElement) -> Product:
    title = product_element.find_element(
        By.CLASS_NAME,
        "title"
    ).get_attribute("title")

    price = (product_element.find_element(
        By.CLASS_NAME, "pull-right"
    ).text.replace("$", ""))

    description = product_element.find_element(
        By.CLASS_NAME,
        "description"
    ).text

    rating_element = product_element.find_element(By.CLASS_NAME, "ratings")
    views = rating_element.find_elements(By.CSS_SELECTOR, "p")
    num_of_reviews = views[0].text.split()[0]
    rating = len(views[-1].find_elements(By.CSS_SELECTOR, "span"))

    return Product(
        title=title,
        description=description,
        price=float(price),
        rating=rating,
        num_of_reviews=int(num_of_reviews)
    )


def load_all_content(driver: WebDriver) -> None:
    if len(driver.find_elements(By.CLASS_NAME,
                                "ecomerce-items-scroll-more")) > 0:
        button = driver.find_element(By.CLASS_NAME,
                                     "ecomerce-items-scroll-more")
        if button.is_displayed():
            ActionChains(driver).click(button).perform()
            load_all_content(driver)


def parse_page(page: str, url: str) -> Product:
    with ChromeDriver() as driver:
        driver.get(url)
        load_all_content(driver)
        products_cards = driver.find_elements(By.CLASS_NAME, "thumbnail")
        products = [extract_product(product) for product in products_cards]
        write_to_csv(
            products=products,
            filename=f"{page}.csv"
        )


def get_all_products() -> None:
    pages_to_scrape = {
        "home": "",
        "computers": "computers",
        "laptops": "computers/laptops",
        "tablets": "computers/tablets",
        "phones": "phones",
        "touch": "phones/touch"
    }

    for page, url in pages_to_scrape.items():
        parse_page(page, f"{HOME_URL}{url}")


def write_to_csv(products: list[Product], filename: str) -> None:
    with open(filename, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(PRODUCTS_FIELDS)

        for product in products:
            writer.writerow(
                [
                    product.title,
                    product.description,
                    product.price,
                    product.rating,
                    product.num_of_reviews
                ]
            )


def main() -> None:
    get_all_products()


if __name__ == "__main__":
    main()
