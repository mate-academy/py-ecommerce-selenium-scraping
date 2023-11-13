import csv
from dataclasses import dataclass, astuple
from time import sleep
from urllib.parse import urljoin
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.common.exceptions import ElementNotInteractableException, ElementClickInterceptedException

PRODUCT_FIELDS = [
    "title", "description", "price", "rating", "num_of_reviews",
]

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")
COMPUTERS_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/computers")
LAPTOPS_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/computers/laptops")
TABLETS_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/computers/tablets")
PHONES_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/phones")
TOUCH_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/phones/touch")

URLS = {
    "home": HOME_URL,
    "computers": COMPUTERS_URL,
    "laptops": LAPTOPS_URL,
    "tablets": TABLETS_URL,
    "phones": PHONES_URL,
    "touch": TOUCH_URL
}


@dataclass
class Product:
    title: str = None
    description: str = None
    price_in_usd: float = None
    rating: int = None
    num_of_reviews: int = None


def write_to_csv(products: list[str], output_csv_path: str) -> None:
    with open(output_csv_path, "w") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(PRODUCT_FIELDS)
        writer.writerows(([astuple(product) for product in products]))


def accept_cookies(driver: webdriver.Chrome) -> None:
    accept_cookies_button = driver.find_elements(By.CLASS_NAME, "acceptCookies")
    sleep(1)

    if accept_cookies_button:
        accept_cookies_button[0].click()


def parse_single_product(driver) -> list[Product]:
    return [
        Product(
            title=card.find_element(By.CLASS_NAME, "title").get_attribute("title"),
            description=card.find_element(By.CLASS_NAME, "description").text,
            price_in_usd=float(card.find_element(By.CLASS_NAME, "price").text[1:]),
            rating=len(card.find_elements(By.CLASS_NAME, "ws-icon-star")),
            num_of_reviews=card.find_element(By.CLASS_NAME, "review-count").text.split(" ")[0],
        ) for card in driver.find_elements(By.CLASS_NAME, "card-body")
    ]


def show_more_products(driver):
    if show_more_button := driver.find_elements(By.CLASS_NAME, "ecomerce-items-scroll-more"):
        while show_more_button[0].is_displayed():
            try:
                show_more_button[0].click()
            except (ElementNotInteractableException, ElementClickInterceptedException):
                print("Element is not clickable")


def get_all_products(urls: dict[str] = URLS) -> None:
    with webdriver.Chrome(service=Service("/usr/bin/chromedriver")) as driver:
        for file_path, list_url in urls.items():
            driver.get(list_url)
            accept_cookies(driver)
            show_more_products(driver)
            products = parse_single_product(driver)
            write_to_csv(products, f"{file_path}.csv")


if __name__ == "__main__":
        get_all_products()
