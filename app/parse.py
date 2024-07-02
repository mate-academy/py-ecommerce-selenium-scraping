import csv
from dataclasses import dataclass
from urllib.parse import urljoin
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.common.action_chains import ActionChains
import time
from typing import Optional, List

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


def setup_driver() -> webdriver.Chrome:
    options = Options()
    options.headless = True
    service = Service("C:/chromedriver/chromedriver.exe")
    driver = webdriver.Chrome(
        service=service,
        options=options
    )
    driver.implicitly_wait(10)
    return driver


def accept_cookies(driver: webdriver.Chrome) -> None:
    try:
        accept_button = WebDriverWait(
            driver,
            10
        ).until(
            ec.element_to_be_clickable(
                (By.ID, "accept-cookie-notification")
            )
        )
        accept_button.click()
    except Exception:
        pass


def parse_product(
        product_element: webdriver.remote.webelement.WebElement
) -> Product:
    title = product_element.find_element(
        By.CLASS_NAME,
        "title"
    ).text
    description = product_element.find_element(
        By.CLASS_NAME,
        "description"
    ).text
    price = float(
        product_element.find_element(
            By.CLASS_NAME,
            "price"
        ).text.replace("$", "")
    )
    rating = len(
        product_element.find_elements(
            By.CLASS_NAME,
            "glyphicon-star"
        )
    )
    num_of_reviews = int(
        product_element.find_element(
            By.CLASS_NAME,
            "ratings"
        ).text.split(" ")[0]
    )
    return Product(
        title,
        description,
        price,
        rating,
        num_of_reviews
    )


def save_to_csv(products: List[Product], filename: str) -> None:
    with open(
        filename,
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
        writer = csv.DictWriter(
            csvfile,
            fieldnames=fieldnames
        )

        writer.writeheader()
        for product in products:
            writer.writerow(
                product.__dict__
            )


def scrape_page(
        driver: webdriver.Chrome,
        url: str, num_products: Optional[int] = None
) -> List[Product]:
    driver.get(url)
    accept_cookies(driver)
    products = []

    if num_products:
        product_elements = driver.find_elements(
            By.CLASS_NAME,
            "thumbnail"
        )[:num_products]
    else:
        while True:
            product_elements = driver.find_elements(
                By.CLASS_NAME,
                "thumbnail"
            )
            try:
                load_more_button = driver.find_element(
                    By.CLASS_NAME,
                    "load-more"
                )
                ActionChains(
                    driver
                ).move_to_element(
                    load_more_button
                ).click(
                    load_more_button
                ).perform()
                time.sleep(2)
            except Exception:
                break

    for product_element in product_elements:
        products.append(
            parse_product(
                product_element
            )
        )

    return products


def get_all_products() -> None:
    driver = setup_driver()

    try:
        pages = {
            "home.csv": (
                urljoin(
                    HOME_URL,
                    ""
                ),
                3
            ),
            "computers.csv": (
                urljoin(
                    HOME_URL,
                    "computers"
                ),
                3
            ),
            "laptops.csv": (
                urljoin(
                    HOME_URL,
                    "computers/laptops"
                ),
                None
            ),
            "tablets.csv": (
                urljoin(
                    HOME_URL,
                    "computers/tablets"
                ),
                None
            ),
            "phones.csv": (
                urljoin(
                    HOME_URL,
                    "phones"
                ),
                3
            ),
            "touch.csv": (
                urljoin(
                    HOME_URL,
                    "phones/touch"
                ),
                None
            )
        }

        for filename, (url, num_products) in pages.items():
            products = scrape_page(
                driver,
                url,
                num_products
            )
            save_to_csv(
                products,
                filename
            )
    finally:
        driver.quit()


if __name__ == "__main__":
    get_all_products()
