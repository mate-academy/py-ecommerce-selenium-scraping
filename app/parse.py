from dataclasses import dataclass
from urllib.parse import urljoin
from selenium import webdriver
from selenium.common import (
    TimeoutException,
    NoSuchElementException,
    ElementNotInteractableException
)
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
import csv
from tqdm import tqdm

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")
PAGE_INFO = [
    (HOME_URL, "home.csv"),
    (urljoin(BASE_URL, "test-sites/e-commerce/more/computers"),
     "computers.csv"),
    (urljoin(BASE_URL, "test-sites/e-commerce/more/computers/laptops"),
     "laptops.csv"),
    (urljoin(BASE_URL, "test-sites/e-commerce/more/computers/tablets"),
     "tablets.csv"),
    (urljoin(BASE_URL, "test-sites/e-commerce/more/phones"), "phones.csv"),
    (urljoin(BASE_URL, "test-sites/e-commerce/more/phones/touch"),
     "touch.csv")
]


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


def get_driver(url: str) -> WebDriver:
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    driver = webdriver.Chrome(options=options)
    driver.get(url)
    return driver


def rating_stars_count(rating_element: WebElement) -> int:
    return len(
        rating_element.find_elements(
            By.TAG_NAME, "p"
        )[1].find_elements(
            By.TAG_NAME, "span"
        )
    )


def get_product_info(product_element: WebElement) -> Product:
    title = product_element.find_element(
        By.CLASS_NAME,
        "title"
    ).get_attribute("title")
    description = product_element.find_element(
        By.CLASS_NAME,
        "description"
    ).text
    price = float(
        product_element.find_element(
            By.CLASS_NAME, "price"
        ).text.replace("$", "").replace(",", ""))
    rating_element = product_element.find_element(By.CLASS_NAME, "ratings")
    rating = rating_stars_count(rating_element)
    num_of_reviews = int(
        rating_element.find_element(
            By.CLASS_NAME, "pull-right"
        ).text.split()[0]
    )
    return Product(
        title=title,
        description=description,
        price=price,
        rating=rating,
        num_of_reviews=num_of_reviews
    )


def accept_cookies(driver: WebDriver) -> None:
    try:
        accept_cookies_button = driver.find_element(
            By.CLASS_NAME,
            "acceptCookies"
        )
        accept_cookies_button.click()
    except ElementNotInteractableException:
        pass
    return


def get_full_page(driver: WebDriver) -> None:
    while True:
        try:
            more_button = driver.find_element(
                By.CLASS_NAME,
                "ecomerce-items-scroll-more"
            )
            more_button.click()
            WebDriverWait(driver, 10).until(
                ec.presence_of_all_elements_located(
                    (By.CLASS_NAME, "ecomerce-items-scroll-more")
                )
            )
        except (
                TimeoutException,
                NoSuchElementException,
                ElementNotInteractableException
        ):
            break
    return


def write_to_csv(filename: str, products: list) -> None:
    with open(filename, mode="w", newline="", encoding="utf-8") as file:
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
                    product.num_of_reviews
                ]
            )
    return


def scrape_page(url: str, filename: str) -> None:
    driver = get_driver(url)

    products = []

    accept_cookies(driver=driver)
    get_full_page(driver=driver)

    product_elements = WebDriverWait(driver, 10).until(
        ec.presence_of_all_elements_located((By.CLASS_NAME, "thumbnail"))
    )

    for product_element in product_elements:
        products.append(get_product_info(product_element))

    write_to_csv(filename=filename, products=products)

    driver.quit()


def get_all_products() -> None:
    for url, filename in tqdm(PAGE_INFO, desc="Scraping pages"):
        scrape_page(url, filename)


if __name__ == "__main__":
    get_all_products()
