import csv
import time
from dataclasses import dataclass, fields, astuple
from urllib.parse import urljoin

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
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


PRODUCT_FIELDS = [field.name for field in fields(Product)]


def get_driver(headless: bool = False):
    options = webdriver.ChromeOptions()
    if headless:
        options.add_argument("--headless")
    return webdriver.Chrome(options=options)


def load_page(driver: webdriver) -> None:
    while True:
        try:
            time.sleep(0.1)
            driver.find_element(By.LINK_TEXT, "More").click()
        except NoSuchElementException:
            break


def close_cookies_banner(driver: webdriver) -> None:
    try:
        driver.find_element(By.ID, "closeCookieBanner").click()
    except NoSuchElementException:
        pass


def get_single_product(product: WebElement) -> Product:
    title = product.find_element(
        By.CLASS_NAME, "title"
    ).get_attribute("title")
    description = product.find_element(By.CLASS_NAME, "description").text
    price = float(product.find_element(By.CLASS_NAME, "price").text[1:])
    rating = len(product.find_elements(By.CLASS_NAME, "glyphicon-star"))
    num_of_reviews = int(product.find_element(
        By.CSS_SELECTOR, "div.ratings > p.pull-right"
    ).text.split()[0])

    return Product(title, description, price, rating, num_of_reviews)


def get_products_on_page(driver: webdriver) -> list[Product]:
    products = []
    product_elements = driver.find_elements(By.CLASS_NAME, "thumbnail")

    for product_element in product_elements:
        product = get_single_product(product_element)
        products.append(product)

    return products


def get_products_by_category(driver: webdriver, category: str) -> None:
    driver.find_element(By.LINK_TEXT, category).click()
    close_cookies_banner(driver)
    load_page(driver)
    driver.execute_script("window.scrollTo(0, 0);")
    products = get_products_on_page(driver)
    write_to_csv(f"{category.lower()}.csv", products)


def write_to_csv(filename: str, products: list[Product]) -> None:
    with open(filename, "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(PRODUCT_FIELDS)
        try:
            writer.writerows([astuple(product) for product in products])
        except csv.Error:
            print(f"Error writing to {filename}")


def get_all_products() -> None:
    driver = get_driver(headless=False)
    driver.implicitly_wait(1)
    driver.get(HOME_URL)

    homepage_products = get_products_on_page(driver)
    write_to_csv("home.csv", homepage_products)

    categories = ("Computers", "Tablets", "Laptops", "Phones", "Touch")

    for category in categories:
        get_products_by_category(driver, category)

    driver.quit()


if __name__ == "__main__":
    get_all_products()
