import csv
from dataclasses import dataclass, fields, astuple
from time import sleep
from urllib.parse import urljoin

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from tqdm import tqdm

from app.driver import SeleniumDriverManager

BASE_URL = "https://webscraper.io/"

HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")

URLS = {
    "home": HOME_URL,
    "phones": urljoin(BASE_URL, HOME_URL + "phones"),
    "touch": urljoin(BASE_URL, HOME_URL + "phones/touch"),
    "computers": urljoin(BASE_URL, HOME_URL + "computers"),
    "tablets": urljoin(BASE_URL, HOME_URL + "computers/tablets"),
    "laptops": urljoin(BASE_URL, HOME_URL + "computers/laptops"),
}


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


class ProductParser:
    PRODUCT_FIELDS = [field.name for field in fields(Product)]

    def __init__(self, urls: dict) -> None:
        self.urls = urls

    @staticmethod
    def parse_single_product(product: WebElement) -> Product:
        return Product(
            title=product.find_element(
                By.CLASS_NAME, "title"
            ).get_property("title"),
            description=product.find_element(
                By.CLASS_NAME, "description"
            ).text,
            price=float(
                product.find_element(
                    By.CLASS_NAME, "price"
                ).text.replace("$", "")
            ),
            rating=len(product.find_elements(By.CLASS_NAME, "ws-icon-star")),
            num_of_reviews=int(
                product.find_element(
                    By.CLASS_NAME, "review-count"
                ).text.split()[0]
            ),
        )

    def write_products_to_csv(
        self, output_csv_path: str, products: list[Product]
    ) -> None:
        with open(
                f"{output_csv_path}.csv", "w", newline="", encoding="utf-8"
        ) as file:
            writer = csv.writer(file)
            writer.writerow(self.PRODUCT_FIELDS)
            writer.writerows([astuple(product) for product in products])

    def get_page_all_products(self) -> None:
        with SeleniumDriverManager.get_driver() as driver:
            for product, url in tqdm(
                self.urls.items(), desc="Processing", unit="product"
            ):
                try:
                    sleep(0.1)
                    print(f"Processing: {product}")

                    driver.get(url)

                    cookies_button = driver.find_elements(
                        By.CLASS_NAME, "acceptCookies"
                    )

                    if cookies_button:
                        cookies_button[0].click()

                    more_button = driver.find_elements(
                        By.CLASS_NAME, "ecomerce-items-scroll-more"
                    )

                    if more_button:
                        more_button = more_button[0]
                        while more_button.is_displayed():
                            more_button.click()
                            sleep(2)

                    products = driver.find_elements(By.CLASS_NAME, "card-body")

                    page_all_products = (
                        [
                            self.parse_single_product(product)
                            for product in products
                        ]
                    )

                    self.write_products_to_csv(product, page_all_products)

                except Exception as e:
                    print(f"Error processing {product}: {str(e)}")

            sleep(0.1)
            print("Finished processing all products! Closing driver...")


def get_all_products() -> None:
    ProductParser(URLS).get_page_all_products()


if __name__ == "__main__":
    get_all_products()
