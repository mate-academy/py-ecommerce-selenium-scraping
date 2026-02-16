import csv
from dataclasses import dataclass
from time import sleep
from urllib.parse import urljoin
from selenium import webdriver
from selenium.common import (
    NoSuchElementException,
    ElementNotInteractableException,
    ElementClickInterceptedException,
)
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.webdriver import WebDriver

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")
COMPUTERS_URL = urljoin(HOME_URL, "computers")
LAPTOPS_URL = urljoin(HOME_URL, "computers/laptops")
TABLETS_URL = urljoin(HOME_URL, "computers/tablets")
PHONES_URL = urljoin(HOME_URL, "phones")
TOUCHES_URL = urljoin(HOME_URL, "phones/touch")

options = Options()
options.add_argument("--headless")
options.add_argument("--window-size=1920,1080")
options.add_argument("--disable-gpu")

_driver = webdriver.Chrome(options=options)


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


def get_driver(url: str) -> WebDriver:
    _driver.get(url)

    return _driver


def close_driver() -> None:
    _driver.quit()


def get_page_data(url: str) -> list[Product]:
    products = []
    driver = get_driver(url=url)

    try:
        cookie_button = driver.find_element(By.CLASS_NAME, "acceptCookies")
        cookie_button.click()
    except NoSuchElementException:
        pass

    try:
        while True:
            more_button = driver.find_element(
                By.CLASS_NAME, "ecomerce-items-scroll-more"
            )
            sleep(0.5)

            if not more_button.is_displayed():
                break

            driver.execute_script("arguments[0].click();", more_button)
    except (
        NoSuchElementException,
        ElementNotInteractableException,
        ElementClickInterceptedException,
    ):
        pass

    product_wrappers = driver.find_elements(By.CLASS_NAME, "product-wrapper")

    for wrapper in product_wrappers:
        title = wrapper.find_element(By.CLASS_NAME, "title").text
        description = wrapper.find_element(By.CLASS_NAME, "description").text
        price_text = wrapper.find_element(By.CLASS_NAME, "price").text
        price = float(price_text.replace("$", ""))

        rating = len(wrapper.find_elements(By.CSS_SELECTOR, "span.ws-icon-star")) # noqa

        reviews_text = wrapper.find_element(
            By.CSS_SELECTOR, ".ratings [itemprop='reviewCount']"
        ).text
        reviews = int(reviews_text)

        products.append(
            Product(
                title=title,
                description=description,
                price=price,
                rating=rating,
                num_of_reviews=reviews,
            )
        )

    return products


def get_all_products() -> None:
    try:
        pages_names = {
            "home.csv": get_page_data(HOME_URL),
            "computer.csv": get_page_data(COMPUTERS_URL),
            "laptop.csv": get_page_data(LAPTOPS_URL),
            "tablet.csv": get_page_data(TABLETS_URL),
            "phone.csv": get_page_data(PHONES_URL),
            "touch.csv": get_page_data(TOUCHES_URL),
        }
    finally:
        close_driver()

    for file_name, products in pages_names.items():
        with open(file_name, "w", encoding="utf-8", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(
                ["title", "description", "price", "rating", "num_of_reviews"]
            )
            for product in products:
                writer.writerow(
                    [
                        product.title,
                        product.description,
                        product.price,
                        product.rating,
                        product.num_of_reviews,
                    ]
                )


if __name__ == "__main__":
    get_all_products()
