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


PAGE_WITH_RANDOM_URLS = {
    MAIN_URL: "home.csv",
    COMPUTERS_URL: "computers.csv",
    PHONES_URL: "phones.csv"
}
PAGINATION_PAGE_URLS = {
    LAPTOPS_URL: "laptops.csv",
    TABLETS_URL: "tablets.csv",
    TOUCH_URL: "touch.csv"
}

BUTTON_COOLDOWN = 0.2


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


ITEMS_FIELDS = [field.name for field in fields(Product)]


def items_to_products(items: list) -> list[Product]:
    result = []
    for item in items:
        result.append(
            Product(
                title=item.find_element(
                    By.CLASS_NAME, "title").get_property("title"
                                                         ),
                description=item.find_element(
                    By.CLASS_NAME, "description"
                ).text,
                price=float(item.find_element(
                    By.CLASS_NAME, "price"
                ).text.replace("$", "")),
                rating=len(item.find_elements(
                    By.CLASS_NAME, "ws-icon-star"
                )),
                num_of_reviews=int(item.find_element(
                    By.CLASS_NAME, "review-count"
                ).text.replace(" reviews", ""))
            )
        )
    return result


def cookie_button_handler(driver: Chrome) -> None:
    cookies_button = driver.find_elements(By.CLASS_NAME, "acceptCookies")
    if cookies_button:
        cookies_button[0].click()
        time.sleep(BUTTON_COOLDOWN)


def parse_main_page(url: str, driver: Chrome) -> list[Product]:
    driver.get(url)

    cookie_button_handler(driver)

    items = driver.find_elements(By.CLASS_NAME, "thumbnail")
    return items_to_products(items)


def parse_full_page(url: str, driver: Chrome) -> list[Product]:
    driver.get(url)

    cookie_button_handler(driver)

    scroll_button = driver.find_element(
        By.CLASS_NAME, "ecomerce-items-scroll-more"
    )
    while scroll_button.is_displayed():
        scroll_button.click()
        time.sleep(BUTTON_COOLDOWN)

    items = driver.find_elements(By.CLASS_NAME, "thumbnail")
    return items_to_products(items)


def write_products_to_csv(csv_path: str, products: list[Product]) -> None:
    with open(csv_path, "w", encoding="utf8", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(ITEMS_FIELDS)
        writer.writerows([astuple(quote) for quote in products])


def get_all_products() -> None:
    chrome_options = Options()
    chrome_options.add_argument("headless")

    driver = Chrome(options=chrome_options)

    for url, filepath in PAGE_WITH_RANDOM_URLS.items():
        products = parse_main_page(url, driver)
        write_products_to_csv(filepath, products)

    for url, filepath in PAGINATION_PAGE_URLS.items():
        products = parse_full_page(url, driver)
        write_products_to_csv(filepath, products)


if __name__ == "__main__":
    get_all_products()
