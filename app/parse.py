import csv
from dataclasses import dataclass, fields, astuple

from selenium.common import NoSuchElementException, TimeoutException
from selenium import webdriver
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions

BASE_URL = "https://webscraper.io/"
PAGES = {
    "home":
        "https://webscraper.io/test-sites/e-commerce/more",
    "computers":
        "https://webscraper.io/test-sites/e-commerce/more/computers",
    "laptops":
        "https://webscraper.io/test-sites/e-commerce/more/computers/laptops",
    "tablets":
        "https://webscraper.io/test-sites/e-commerce/more/computers/tablets",
    "phones":
        "https://webscraper.io/test-sites/e-commerce/more/phones",
    "touch":
        "https://webscraper.io/test-sites/e-commerce/more/phones/touch",
}


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


PRODUCT_FIELDS = [field.name for field in fields(Product)]


def parse_single_product(product_card: WebElement) -> Product:
    return Product(
        title=product_card.find_element(
            By.CSS_SELECTOR, ".title"
        ).get_attribute("title"),
        description=product_card.find_element(
            By.CSS_SELECTOR, "[itemprop='description']"
        ).text,
        price=float(product_card.find_element(
            By.CSS_SELECTOR, ".price"
        ).text.replace("$", "")),
        rating=len(
            product_card.find_elements(By.CSS_SELECTOR, ".ws-icon-star")
        ),
        num_of_reviews=int(
            product_card.find_element(
                By.CSS_SELECTOR, "[itemprop='reviewCount']"
            ).text
        ),
    )


def write_products_to_csv(products: list[Product], name_page: str) -> None:
    with open(f"{name_page}.csv", "w") as f:
        writer = csv.writer(f)
        writer.writerow(PRODUCT_FIELDS)
        writer.writerows([astuple(product) for product in products])


def accept_cookies(driver: WebDriver) -> None:
    try:
        (WebDriverWait(driver, 5)
         .until(
            expected_conditions.element_to_be_clickable(
                (By.CSS_SELECTOR, "[data-tid='banner-accept']")
            )
        ).click())
    except TimeoutException:
        pass


def click_more_button(driver: WebDriver) -> None:
    try:
        more_bttn = driver.find_element(
            By.CSS_SELECTOR, ".ecomerce-items-scroll-more"
        )
    except NoSuchElementException:
        return
    while more_bttn.is_displayed():
        cards_before = len(
            driver.find_elements(By.CSS_SELECTOR, ".product-wrapper")
        )
        more_bttn.click()
        WebDriverWait(driver, 5).until(
            lambda d: len(
                d.find_elements(By.CSS_SELECTOR, ".product-wrapper")
            ) > cards_before
        )


def get_all_products() -> None:
    with webdriver.Chrome() as driver:
        for name_page, page_url in PAGES.items():
            driver.get(page_url)
            accept_cookies(driver)
            click_more_button(driver)
            product_cards = driver.find_elements(
                By.CSS_SELECTOR, ".product-wrapper.card-body"
            )
            products = []
            for product_card in product_cards:
                products.append(parse_single_product(product_card))
            write_products_to_csv(products=products, name_page=name_page)


if __name__ == "__main__":
    get_all_products()
