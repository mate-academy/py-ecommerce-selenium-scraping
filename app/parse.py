import csv
from dataclasses import dataclass
from time import sleep
from urllib.parse import urljoin

from selenium.webdriver import Chrome
from selenium.webdriver.common.by import By
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


def parse_single_product(card: WebElement) -> Product:
    title = card.find_element(By.CLASS_NAME, "title").get_attribute("title")
    description = card.find_element(By.CLASS_NAME, "description").text
    price = float(
        card.find_element(By.CLASS_NAME, "price").text.replace("$", "")
    )
    rating_block = card.find_element(By.CLASS_NAME, "ratings")
    data_rating = len(
        rating_block.find_elements(By.CLASS_NAME, "ws-icon-star")
    )
    num_of_reviews = int(
        rating_block.find_element(By.CLASS_NAME, "review-count").text.replace(
            " reviews", ""
        )
    )

    return Product(
        title=title,
        description=description,
        price=price,
        rating=data_rating,
        num_of_reviews=num_of_reviews,
    )


def parse_products(driver: Chrome, product_url: str) -> list[Product]:
    driver.get(urljoin(HOME_URL, product_url))
    accept_cookies(driver)
    load_all_products(driver)
    cards = driver.find_elements(By.CLASS_NAME, "card-body")
    products = [parse_single_product(card) for card in cards]

    return products


def accept_cookies(driver: Chrome) -> None:
    cookies = driver.find_elements(By.CSS_SELECTOR, "a.acceptCookies")

    if cookies:
        cookies[0].click()
        sleep(0.5)


def load_all_products(driver: Chrome) -> None:
    button_more = driver.find_elements(
        By.CLASS_NAME, "ecomerce-items-scroll-more"
    )

    while button_more:
        if button_more[0].get_attribute("style"):
            break

        button_more[0].click()
        sleep(0.5)


def get_all_products() -> None:
    driver = Chrome()

    home_page_products = parse_products(driver, "")
    computers_page_products = parse_products(driver, "computers")
    laptops_page_products = parse_products(driver, "computers/laptops")
    tablets_page_products = parse_products(driver, "computers/tablets")
    phones_page_products = parse_products(driver, "phones")
    touch_page_products = parse_products(driver, "phones/touch")

    write_to_csv(home_page_products, "home.csv")
    write_to_csv(computers_page_products, "computers.csv")
    write_to_csv(laptops_page_products, "laptops.csv")
    write_to_csv(tablets_page_products, "tablets.csv")
    write_to_csv(phones_page_products, "phones.csv")
    write_to_csv(touch_page_products, "touch.csv")


def write_to_csv(products: list[Product], output_csv_path: str) -> None:
    with open(output_csv_path, "w", newline="", encoding="utf-8") as file:
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
