import csv
from dataclasses import dataclass, fields
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import (
    NoSuchElementException,
    ElementClickInterceptedException,
    ElementNotInteractableException,
    TimeoutException,
)
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions

BASE_URL = "https://webscraper.io/"

PAGES = {
    "home": "test-sites/e-commerce/more/",
    "computers": "test-sites/e-commerce/more/computers",
    "phones": "test-sites/e-commerce/more/phones",
    "laptops": "test-sites/e-commerce/more/computers/laptops",
    "tablets": "test-sites/e-commerce/more/computers/tablets",
    "touch": "test-sites/e-commerce/more/phones/touch",
}


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


FIELD_NAMES = [field.name for field in fields(Product)]


def initialize_driver() -> WebDriver:
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--headless")
    return webdriver.Chrome(options=chrome_options)


def handle_cookies(driver: WebDriver) -> None:
    try:
        accept_cookies = driver.find_element(By.CLASS_NAME, "acceptCookies")
        accept_cookies.click()
    except (NoSuchElementException, TimeoutException,
            ElementClickInterceptedException, ElementNotInteractableException):
        pass


def click_show_more(driver: WebDriver) -> None:
    while True:
        try:
            more_button = WebDriverWait(driver, 5).until(
                expected_conditions.element_to_be_clickable((
                    By.CSS_SELECTOR,
                    ".btn.ecomerce-items-scroll-more"
                ))
            )
            more_button.click()
        except (NoSuchElementException, ElementNotInteractableException,
                TimeoutException, ElementClickInterceptedException):
            break


def parse_single_product(soup: BeautifulSoup) -> Product:
    rating_soup = soup.select_one(".ratings > p[data-rating]") or {}
    rating = int(rating_soup.get("data-rating", 5))

    title_elem = soup.select_one(".title")
    description_elem = soup.select_one(".description")
    price_elem = soup.select_one(".price")
    reviews_elem = soup.select_one(".ratings > p.pull-right")

    title = title_elem.get("title", "")
    description = description_elem.text.replace(
        "\xa0",
        " "
    ) if description_elem else ""
    price = float(price_elem.text.replace("$", "")) if price_elem else 0.0
    num_of_reviews = int(reviews_elem.text.split()[0]) if reviews_elem else 0

    return Product(
        title=title,
        description=description,
        price=price, rating=rating,
        num_of_reviews=num_of_reviews
    )


def write_product_to_csv(products: list[Product], path: str) -> None:
    with open(path, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(FIELD_NAMES)
        for product in products:
            writer.writerow(
                [product.title,
                 product.description,
                 product.price,
                 product.rating,
                 product.num_of_reviews]
            )


def get_all_products() -> None:
    driver = initialize_driver()
    for name, link in PAGES.items():
        driver.get(urljoin(BASE_URL, link))
        click_show_more(driver)
        handle_cookies(driver)

        html_code = driver.page_source
        soup = BeautifulSoup(html_code, "html.parser")
        products_soup = soup.select(".thumbnail")
        products = [parse_single_product(product) for product in products_soup]

        write_product_to_csv(products, f"{name}.csv")

    driver.close()


if __name__ == "__main__":
    get_all_products()
