import time
import csv
from dataclasses import dataclass, fields, astuple
from urllib.parse import urljoin

from tqdm import tqdm
from selenium.common import NoSuchElementException
from selenium.webdriver import Firefox
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.webdriver import WebDriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.remote.webelement import WebElement

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")

COMPUTER_URL = urljoin(HOME_URL, "computers/")
PHONE_URL = urljoin(HOME_URL, "phones/")

LAPTOP_URL = urljoin(COMPUTER_URL, "laptops")
TABLET_URL = urljoin(COMPUTER_URL, "tablets")

TOUCH_URL = urljoin(PHONE_URL, "touch")

URLS_TO_SCRAPE = {
    HOME_URL: "home.csv",
    COMPUTER_URL: "computers.csv",
    PHONE_URL: "phones.csv",
    LAPTOP_URL: "laptops.csv",
    TABLET_URL: "tablets.csv",
    TOUCH_URL: "touch.csv"
}


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


PRODUCT_FIELDS = [field.name for field in fields(Product)]


def parse_single_product(product: WebElement) -> Product:
    return Product(
        title=product.find_element(
            By.CLASS_NAME, "title"
        ).get_attribute("title"),
        description=product.find_element(By.CLASS_NAME, "description").text,
        price=float(
            product.find_element(By.CLASS_NAME, "price")
            .text.replace("$", "")
        ),
        rating=len(
            product.find_elements(By.CLASS_NAME, "ws-icon-star")
        ),
        num_of_reviews=int(
            product.find_element(By.CLASS_NAME, "review-count")
            .text.split()[0]
        )
    )


def write_products_to_csv(csv_path: str, products: list[Product]) -> None:
    with open(csv_path, "w") as f:
        writer = csv.writer(f)
        writer.writerow(PRODUCT_FIELDS)
        writer.writerows([astuple(product) for product in products])


def get_single_page_products(webdriver: WebDriver) -> list[Product]:
    time.sleep(0.5)
    try:
        cookie_button = webdriver.find_element(By.CLASS_NAME, "acceptCookies")
        cookie_button.click()
    except NoSuchElementException:
        pass

    product_elements = webdriver.find_elements(By.CLASS_NAME, "card-body")
    products = product_elements

    try:
        button_more = webdriver.find_element(
            By.CLASS_NAME,
            "ecomerce-items-scroll-more"
        )

        pbar = tqdm(desc="Loading more products", unit="batch")
        while button_more.is_displayed():
            button_more.click()

            product_elements = webdriver.find_elements(
                By.CLASS_NAME,
                "card-body"
            )

            if len(product_elements) <= len(products):
                break

            pbar.update(len(product_elements) - len(products))
            products = product_elements

            time.sleep(0.5)

    except NoSuchElementException:
        pass

    return [parse_single_product(product) for product in products]


def get_all_products() -> None:
    options = Options()
    options.add_argument("--headless")

    webdriver = Firefox(options=options)

    for url, output_path in tqdm(
        URLS_TO_SCRAPE.items(), desc="Scraping pages", unit="page"
    ):
        webdriver.get(url)
        print(f"\nProcessing: {url} -> {output_path}")

        products = get_single_page_products(webdriver)
        write_products_to_csv(output_path, products)

    webdriver.close()


if __name__ == "__main__":
    get_all_products()
