import csv
from dataclasses import dataclass
from time import sleep
from urllib.parse import urljoin

from selenium import webdriver
from selenium.common import NoSuchElementException
from selenium.webdriver import ChromeOptions, Chrome
from selenium.webdriver.common.by import By

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


def initialize_driver() -> webdriver:
    options = ChromeOptions()
    options.add_argument("--headless")
    return Chrome(options=options)


def accept_cookies(driver: webdriver) -> None:
    try:
        cookie_btn = driver.find_element(
            By.CLASS_NAME, "acceptCookies"
        )
        cookie_btn.click()
    except NoSuchElementException:
        pass


def get_links_and_rating_data(driver: webdriver) -> dict:
    links_with_titles = {}
    products = driver.find_elements(
        By.CLASS_NAME, "thumbnail"
    )

    for product in products:
        title = product.find_element(
            By.CLASS_NAME,
            "title"
        )
        link = title.get_attribute("href")

        rating = len(product.find_elements(
            By.CLASS_NAME, "ws-icon-star"
        ))
        reviews_count = int(product.find_element(
            By.CSS_SELECTOR, ".ratings > p"
        ).text.split()[0])

        links_with_titles[link] = {
            "rating": rating,
            "reviews_count": reviews_count,
        }

    return links_with_titles


def parse_product_detail_page(link: str,
                              rating: int,
                              reviews_count: int,
                              driver: webdriver) -> Product:
    driver.get(link)
    title = driver.find_element(
        By.CLASS_NAME, "caption"
    ).find_element(
        By.XPATH, ".//h4[not(@class)]"
    ).text
    price = float(driver.find_element(
        By.CLASS_NAME, "price"
    ).text.replace("$", ""))
    description = driver.find_element(
        By.CLASS_NAME, "description"
    ).text

    return Product(
        title=title,
        description=description,
        price=price,
        rating=rating,
        num_of_reviews=reviews_count,
    )


def parse_page(page_url: str,
               driver: webdriver) -> list[Product]:
    driver.get(page_url)
    accept_cookies(driver)
    try:
        more_btn = driver.find_element(
            By.CLASS_NAME,
            "ecomerce-items-scroll-more"
        )
        while more_btn.is_displayed():
            more_btn.click()
            sleep(0.25)

    except NoSuchElementException:
        pass
    links_and_rating_data = get_links_and_rating_data(driver)
    return [
        parse_product_detail_page(
            link,
            data["rating"],
            data["reviews_count"],
            driver
        )
        for link, data in links_and_rating_data.items()
    ]


def parsed_data_to_csv(filename: str, data: list) -> None:
    with open(filename, "w", newline="") as target_file:
        writer = csv.writer(target_file)
        writer.writerow(
            [
                "title",
                "description",
                "price",
                "rating",
                "num_of_reviews"
            ]
        )

        for product in data:

            writer.writerow(
                [
                    product.title,
                    product.description,
                    product.price,
                    product.rating,
                    product.num_of_reviews
                ]
            )


def get_all_products() -> None:
    driver = initialize_driver()
    target_files_with_pages = {
        "home.csv": HOME_URL,
        "computers.csv": urljoin(HOME_URL, "computers"),
        "tablets.csv": urljoin(HOME_URL, "computers/tablets"),
        "laptops.csv": urljoin(HOME_URL, "computers/laptops"),
        "phones.csv": urljoin(HOME_URL, "phones"),
        "touch.csv": urljoin(HOME_URL, "phones/touch"),
    }

    for filename, page_url in target_files_with_pages.items():
        parsed_data = parse_page(page_url, driver)
        parsed_data_to_csv(filename, parsed_data)


if __name__ == "__main__":
    get_all_products()
