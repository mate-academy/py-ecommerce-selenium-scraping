import csv

from dataclasses import dataclass
from urllib.parse import urljoin

from selenium import webdriver
from selenium.common import (
    ElementNotInteractableException,
    ElementClickInterceptedException,
)
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote import webelement

from tqdm import tqdm

BASE_URL = "https://webscraper.io/"


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


def get_webdriver() -> WebDriver:
    chrome_options = webdriver.ChromeOptions()

    chrome_options.add_argument("--headless")

    return webdriver.Chrome(options=chrome_options)


def get_page(
        common_part: str,
        path: str,
        driver: WebDriver
) -> None:
    page = urljoin(BASE_URL, common_part + path)
    driver.get(page)


def get_product(product_item: webelement) -> Product:
    title = product_item.find_element(
        By.CLASS_NAME, "title"
    ).get_attribute("title")
    description = product_item.find_element(
        By.CLASS_NAME, "description"
    ).text
    price = float(product_item.find_element(
        By.CLASS_NAME, "price"
    ).text.replace("$", ""))
    rating = len(product_item.find_elements(
        By.CLASS_NAME, "ws-icon-star"
    ))
    num_of_reviews = int(product_item.find_element(
        By.CSS_SELECTOR, "p.pull-right"
    ).text.split()[0])

    return Product(
        title=title,
        description=description,
        price=price,
        rating=rating,
        num_of_reviews=num_of_reviews,
    )


def get_product_list(
        products_webelements: list[webelement],
        page_name: str
) -> list[Product]:
    return [
        get_product(product)
        for product
        in tqdm(
            products_webelements,
            desc=f"Creating product list from {page_name} page"
        )
    ]


def write_in_csv_file(
        file_name: str,
        product_list: list[Product]
) -> None:
    with open(
            file_name,
            "w",
            newline="",
            encoding="utf-8"
    ) as csvfile:
        fieldnames = [
            "title",
            "description",
            "price",
            "rating",
            "num_of_reviews"
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()

        for product in product_list:
            writer.writerow({
                "title": product.title,
                "description": product.description,
                "price": product.price,
                "rating": product.rating,
                "num_of_reviews": product.num_of_reviews,
            })


def accept_cookies(driver: WebDriver) -> None:
    accept_cookies_banner = driver.find_elements(
        By.CSS_SELECTOR, "a.acceptCookies"
    )

    if accept_cookies_banner:
        accept_cookies_banner[0].click()


def is_more_button(driver: WebDriver) -> bool:
    more_button = driver.find_elements(
        By.CLASS_NAME, "ecomerce-items-scroll-more"
    )

    if more_button:
        try:
            more_button[0].click()
        except ElementNotInteractableException:
            return False
        except ElementClickInterceptedException:
            return False
        else:
            return True

    return False


def get_all_products() -> None:
    driver = get_webdriver()

    common_href_part = "test-sites/e-commerce/more/"
    pages_info = {
        "home": ["", "home.csv"],
        "computers": ["computers", "computers.csv"],
        "laptops": ["computers/laptops", "laptops.csv"],
        "tablets": ["computers/tablets", "tablets.csv"],
        "phones": ["phones", "phones.csv"],
        "touch": ["phones/touch", "touch.csv"],
    }

    for page_name, page_info in pages_info.items():
        path, file_name = page_info
        get_page(common_href_part, path, driver)

        if page_name == "home":
            accept_cookies(driver)

        if page_name in ("laptops", "tablets", "touch"):
            is_more_products = True

            while is_more_products:
                is_more_products = is_more_button(driver)

        products_webelements = driver.find_elements(
            By.CLASS_NAME, "thumbnail"
        )
        product_list = get_product_list(
            products_webelements, page_name
        )

        write_in_csv_file(file_name, product_list)

    driver.close()


if __name__ == "__main__":
    get_all_products()
