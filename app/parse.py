import csv
from dataclasses import dataclass
from time import sleep
from urllib.parse import urljoin

from selenium import webdriver
from selenium.common import NoSuchElementException
from selenium.webdriver import Chrome, ChromeOptions

from selenium.webdriver.common.by import By
from selenium.webdriver.remote import webelement

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int

    @classmethod
    def from_dict(cls, data: dict) -> "Product":
        return cls(**data)


def get_driver() -> webdriver:
    options = ChromeOptions()
    options.add_argument("--headless")
    return Chrome(options=options)


def get_data(block: webelement, ratings_from_global_page: dict) -> dict:
    price = float(block.find_element(
        By.CLASS_NAME, "price"
    ).text[1:])

    return {
        "title": block.find_element(
            By.XPATH, ".//h4[not(@class)]"
        ).text,
        "description": block.find_element(
            By.CLASS_NAME, "description"
        ).text,
        "price": price,
        "rating": ratings_from_global_page["rating"],
        "num_of_reviews": ratings_from_global_page["reviews"]
    }


def parse_item_page(link: str, ratings: dict, driver: webdriver) -> Product:
    driver.get(link)
    block = driver.find_element(By.CLASS_NAME, "thumbnail")
    data = get_data(block, ratings)
    return Product.from_dict(data)


def get_links_with_proper_rating(driver: webdriver) -> dict:
    res = {}
    for el in driver.find_elements(
        By.CLASS_NAME, "thumbnail"
    ):
        link = el.find_element(
            By.CLASS_NAME,
            "title"
        ).get_attribute("href")

        rating = el.find_elements(
            By.CLASS_NAME, "ws-icon-star"
        )

        reviews = int(el.find_element(
            By.CSS_SELECTOR, ".ratings > p"
        ).text.split()[0])

        res[link] = {
            "rating": len(rating),
            "reviews": reviews
        }
    return res


def accept_cookies(driver: webdriver) -> None:
    try:
        cookie_btn = driver.find_element(
            By.CLASS_NAME, "acceptCookies"
        )
        cookie_btn.click()
    except NoSuchElementException:
        pass


def parse_page(url: str, driver: webdriver) -> list[Product]:
    driver.get(url)
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

    links = get_links_with_proper_rating(driver)

    return [
        parse_item_page(link, ratings, driver)
        for link, ratings in links.items()
    ]


def to_csv(data: list, filename: str) -> None:
    with open(filename, "w", newline="") as file:
        writer = csv.writer(file)
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
    driver = get_driver()

    pages_to_parse = [
        ("home.csv", HOME_URL),
        ("computers.csv", urljoin(HOME_URL, "computers")),
        ("tablets.csv", urljoin(HOME_URL, "computers/tablets")),
        ("laptops.csv", urljoin(HOME_URL, "computers/laptops")),
        ("phones.csv", urljoin(HOME_URL, "phones")),
        ("touch.csv", urljoin(HOME_URL, "phones/touch")),

    ]

    for page in pages_to_parse:
        data = parse_page(page[1], driver)
        to_csv(data, page[0])


if __name__ == "__main__":
    get_all_products()
