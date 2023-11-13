import csv
import time
from dataclasses import dataclass, fields, astuple

from selenium.webdriver import Chrome
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By

BASE_URL = "https://webscraper.io/test-sites/e-commerce/more/"
PRODUCT_URL = {
    "tablets": "computers/tablets",
    "home": "",
    "phones": "phones",
    "touch": "phones/touch",
    "computers": "computers",
    "laptops": "computers/laptops",
}


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


PRODUCT_FIELDS = [field.name for field in fields(Product)]


def get_page_product(url: str, driver: WebDriver) -> list:
    driver.get(url)

    cookies = driver.find_elements(By.CLASS_NAME, "acceptCookies")

    if cookies:
        cookies[0].click()

    more_button = driver.find_elements(
        By.CLASS_NAME, "ecomerce-items-scroll-more"
    )

    if more_button:
        more_button = more_button[0]
        while more_button and more_button.is_displayed():
            more_button.click()
            time.sleep(0.1)

    cards = driver.find_elements(By.CLASS_NAME, "card")

    cards_list = []

    for card in cards:
        title = card.find_element(
            By.CLASS_NAME, "title"
        ).get_attribute("title")
        description = card.find_element(By.CLASS_NAME, "description").text
        price = float(card.find_element(
            By.CLASS_NAME, "price"
        ).text.replace("$", ""))
        rating = len(card.find_elements(By.CLASS_NAME, "ws-icon-star"))
        num_of_reviews = int(
            card.find_element(By.CLASS_NAME, "review-count").text.split()[0]
        )
        cards_list.append(
            Product(
                title=title,
                description=description,
                price=price,
                rating=rating,
                num_of_reviews=num_of_reviews,
            )
        )
    return cards_list


def write_product_to_csv(
        products: list[Product],
        output_csv_path: str
) -> None:
    with open(output_csv_path, "w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(PRODUCT_FIELDS)
        writer.writerows([astuple(product) for product in products])


def get_all_products() -> None:
    driver = Chrome()
    for name, url in PRODUCT_URL.items():
        page_url = BASE_URL + url
        list_of_products = get_page_product(page_url, driver)
        write_product_to_csv(list_of_products, f"{name}.csv")


if __name__ == "__main__":
    get_all_products()
