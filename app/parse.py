import csv
import time
from dataclasses import dataclass, fields, astuple
from urllib.parse import urljoin

from selenium.webdriver import Chrome
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By


BASE_URL = "https://webscraper.io/"
MAIN_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")
COMPUTERS_URL = urljoin(MAIN_URL, "computers/")
PHONES_URL = urljoin(MAIN_URL, "phones/")
LAPTOPS_URL = urljoin(COMPUTERS_URL, "laptops")
TABLETS_URL = urljoin(COMPUTERS_URL, "tablets")
TOUCH_URL = urljoin(PHONES_URL, "touch")


NAMES_FOR_CSV = {
    MAIN_URL: "home.csv",
    COMPUTERS_URL: "computers.csv",
    PHONES_URL: "phones.csv",
    LAPTOPS_URL: "laptops.csv",
    TABLETS_URL: "tablets.csv",
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


def get_products_by_type(products: list) -> list[Product]:
    return [
        Product(
            title=product.find_element(
                By.CLASS_NAME, "title").get_property("title"),
            description=product.find_element(
                By.CLASS_NAME, "description"
            ).text,
            price=float(product.find_element(
                By.CLASS_NAME, "price"
            ).text.replace("$", "")),
            rating=len(product.find_elements(
                By.CLASS_NAME, "ws-icon-star"
            )),
            num_of_reviews=int(product.find_element(
                By.CLASS_NAME, "review-count"
            ).text.split()[0])
        ) for product in products
    ]


def cookie_button_handler(driver: Chrome) -> None:
    cookies_button = driver.find_elements(By.CLASS_NAME, "acceptCookies")
    if cookies_button:
        cookies_button[0].click()
        time.sleep(0.5)


def parse_page(url: str, driver: Chrome) -> list[Product]:
    driver.get(url)
    cookie_button_handler(driver)

    scroll_button = driver.find_elements(
        By.CLASS_NAME, "ecomerce-items-scroll-more"
    )

    if scroll_button:
        while scroll_button[0].is_displayed():
            scroll_button[0].click()
            time.sleep(0.5)

    products = driver.find_elements(By.CLASS_NAME, "thumbnail")

    return get_products_by_type(products)


def write_to_csv(csv_filename: str, products: list[Product]) -> None:
    with open(csv_filename, "w", newline="", encoding="utf8") as file:
        writer = csv.writer(file)
        writer.writerow(PRODUCT_FIELDS)
        writer.writerows([astuple(quote) for quote in products])


def get_all_products() -> None:
    chrome_options = Options()
    chrome_options.add_argument("headless")

    driver = Chrome(options=chrome_options)

    for url, filename in NAMES_FOR_CSV.items():
        products = parse_page(url, driver)
        write_to_csv(filename, products)


if __name__ == "__main__":
    get_all_products()
