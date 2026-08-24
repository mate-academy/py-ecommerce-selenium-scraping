import csv
import time
from dataclasses import astuple, dataclass
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import (
    ElementClickInterceptedException,
    NoSuchElementException,
    TimeoutException,
)
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as conditions
from selenium.webdriver.support.ui import WebDriverWait
from tqdm import tqdm


BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")

PAGES = {
    "home": HOME_URL,
    "computers": urljoin(HOME_URL, "computers"),
    "laptops": urljoin(HOME_URL, "computers/laptops"),
    "tablets": urljoin(HOME_URL, "computers/tablets"),
    "phones": urljoin(HOME_URL, "phones"),
    "touch": urljoin(HOME_URL, "phones/touch"),
}


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


def get_driver() -> WebDriver:
    options = Options()
    options.add_argument("--headless=new")
    return webdriver.Chrome(options=options)


def accept_cookies(driver: WebDriver) -> None:
    try:
        button = WebDriverWait(driver, 5).until(
            conditions.element_to_be_clickable(
                (By.CSS_SELECTOR, "[data-tid='banner-accept']")
            )
        )
        button.click()
    except TimeoutException:
        pass


def click_all_more_buttons(driver: WebDriver) -> None:
    while True:
        try:
            more_button = driver.find_element(
                By.CLASS_NAME, "ecomerce-items-scroll-more"
            )
        except NoSuchElementException:
            return

        if not more_button.is_displayed():
            return

        try:
            more_button.click()
        except ElementClickInterceptedException:
            accept_cookies(driver)
            more_button.click()

        time.sleep(0.3)


def clean_text(text: str) -> str:
    return text.replace("\xa0", " ")


def parse_single_product(product_soup: BeautifulSoup) -> Product:
    price = product_soup.select_one(".price").text.replace("$", "")
    reviews = product_soup.select_one(
        ".review-count [itemprop='reviewCount']"
    ).text

    return Product(
        title=clean_text(product_soup.select_one(".title")["title"]),
        description=clean_text(
            product_soup.select_one(".description").text
        ),
        price=float(price),
        rating=len(product_soup.select(".ws-icon-star")),
        num_of_reviews=int(reviews),
    )


def get_single_page_products(driver: WebDriver, url: str) -> list[Product]:
    driver.get(url)
    WebDriverWait(driver, 10).until(
        conditions.presence_of_element_located((By.CLASS_NAME, "thumbnail"))
    )
    click_all_more_buttons(driver)

    page_soup = BeautifulSoup(driver.page_source, "html.parser")
    products = page_soup.select(".thumbnail")
    return [parse_single_product(product) for product in products]


def write_products_to_csv(
    products: list[Product], output_csv_path: str
) -> None:
    with open(output_csv_path, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(
            ["title", "description", "price", "rating", "num_of_reviews"]
        )
        writer.writerows(astuple(product) for product in products)


def get_all_products() -> None:
    driver = get_driver()

    try:
        driver.get(HOME_URL)
        accept_cookies(driver)

        for name, url in tqdm(PAGES.items(), desc="Scraping pages"):
            products = get_single_page_products(driver, url)
            write_products_to_csv(products, f"{name}.csv")
    finally:
        driver.quit()


if __name__ == "__main__":
    get_all_products()
