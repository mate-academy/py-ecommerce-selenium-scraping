import csv
from dataclasses import dataclass, astuple
from urllib.parse import urljoin

from selenium import webdriver
from selenium.common import TimeoutException
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait

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


def accept_cookies(driver: WebDriver) -> None:
    try:
        WebDriverWait(driver, 5).until(
            ec.element_to_be_clickable((By.CSS_SELECTOR, '[data-tid="banner-accept"]'))
        ).click()
    except TimeoutException:
        pass


def scrape_page(driver: WebDriver, url: str) -> list[Product]:
    driver.get(url)
    accept_cookies(driver)
    while True:
        buttons = driver.find_elements(By.CLASS_NAME, "ecomerce-items-scroll-more")

        if not buttons:
            break

        button = buttons[0]

        if not button.is_displayed():
            break

        previous_count = len(driver.find_elements(By.CLASS_NAME, "product-wrapper"))

        button.click()

        WebDriverWait(driver, 10).until(
            lambda driver: len(driver.find_elements(By.CLASS_NAME, "product-wrapper"))
            > previous_count
        )

    products = driver.find_elements(By.CLASS_NAME, "product-wrapper")
    products_list = []
    for product in products:
        title = product.find_element(By.CLASS_NAME, "title").get_attribute("title")
        description = product.find_element(By.CLASS_NAME, "description").text
        price = float(
            product.find_element(By.CLASS_NAME, "price").text.replace("$", "")
        )
        rating = len(product.find_elements(By.CLASS_NAME, "ws-icon-star"))
        num_of_reviews = int(
            product.find_element(By.CSS_SELECTOR, '[itemprop="reviewCount"]').text
        )
        parsed_product = Product(
            title=title,
            description=description,
            price=price,
            rating=rating,
            num_of_reviews=num_of_reviews,
        )
        products_list.append(parsed_product)
    return products_list


def csv_formating(path: str, products: list[Product]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["title", "description", "price", "rating", "num_of_reviews"])
        writer.writerows(astuple(product) for product in products)


def get_all_products() -> None:
    driver = webdriver.Chrome()
    try:
        for name, url in PAGES.items():
            products = scrape_page(driver, url)
            csv_formating(f"{name}.csv", products)
    finally:
        driver.quit()


if __name__ == "__main__":
    get_all_products()
