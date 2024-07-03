import csv
import time
from dataclasses import dataclass
from urllib.parse import urljoin

from selenium import webdriver
from selenium.common import NoSuchElementException
from selenium.webdriver.common.by import By
from tqdm import tqdm

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")
COMPUTERS_URL = urljoin(HOME_URL, "computers")
LAPTOPS_URL = urljoin(HOME_URL, "computers/laptops")
TABLETS_URL = urljoin(HOME_URL, "computers/tablets")
PHONES_URL = urljoin(HOME_URL, "phones")
TOUCH_URL = urljoin(HOME_URL, "phones/touch")

options = webdriver.ChromeOptions()
options.add_argument("--headless")


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


def save_to_csv(file_name: str, products: list[Product]) -> None:
    with open(file_name, "w", newline="") as file:
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


class ProductParser:
    def __init__(self, driver: webdriver.Chrome) -> None:
        self.driver = driver
        self.cookies_accepted = False

    def parse_page(self, url: str, file_name: str) -> list[Product]:
        self.driver.get(url)
        if not self.cookies_accepted:
            self.accept_cookies()
        self.handle_pagination()
        items = self.driver.find_elements(By.CLASS_NAME, "product-wrapper")
        products = []
        with tqdm(total=len(items),
                  desc="Parsing Products", unit_scale=True) as pbar:
            for item in items:
                title = item.find_element(By.CLASS_NAME,
                                          "title").get_attribute("title")
                description = item.find_element(
                    By.CLASS_NAME,
                    "description"
                ).text
                price = float(item.find_element(
                    By.CLASS_NAME,
                    "price"
                ).text[1:])
                rating = len(item.find_elements(
                    By.CLASS_NAME,
                    "ws-icon-star"
                ))
                num_of_reviews = int(item.find_element(
                    By.CLASS_NAME,
                    "review-count"
                ).text.split()[0])
                products.append(Product(title, description,
                                        price, rating, num_of_reviews))
                pbar.update(1)
        save_to_csv(file_name, products)
        return products

    def accept_cookies(self) -> None:
        try:
            cookies_accept = self.driver.find_element(By.CLASS_NAME,
                                                      "acceptCookies")
            cookies_accept.click()
        except NoSuchElementException:
            print("Cookies were already accepted (accept button not found)")
        self.cookies_accepted = True

    def handle_pagination(self) -> None:
        while True:
            try:
                pagination_button = self.driver.find_element(
                    By.CLASS_NAME,
                    "ecomerce-items-scroll-more"
                )
                if pagination_button.is_displayed():
                    pagination_button.click()
                    time.sleep(0.1)
                else:
                    break
            except NoSuchElementException:
                break
        time.sleep(1)


def get_all_products() -> None:
    with webdriver.Chrome(options=options) as driver:
        parser = ProductParser(driver)
        for category, url, file_name in [
            ("Home products", HOME_URL, "home.csv"),
            ("Computer products", COMPUTERS_URL, "computers.csv"),
            ("Laptop products", LAPTOPS_URL, "laptops.csv"),
            ("Tablet products", TABLETS_URL, "tablets.csv"),
            ("Phone products", PHONES_URL, "phones.csv"),
            ("Touch products", TOUCH_URL, "touch.csv"),
        ]:
            print(category)
            parser.parse_page(url, file_name)


if __name__ == "__main__":
    get_all_products()
