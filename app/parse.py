import csv
import time
from dataclasses import dataclass, fields, astuple
from urllib.parse import urljoin

from selenium import webdriver
from selenium.common import NoSuchElementException
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


def get_driver(headless: bool = False) -> webdriver:
    options = webdriver.ChromeOptions()
    if headless:
        options.add_argument("--headless")
    return webdriver.Chrome(options=options)


def get_single_product(product: WebElement) -> Product:
    return Product(
        title=product.find_element(By.CLASS_NAME, "title").get_attribute(
            "title"
        ),
        description=product.find_element(By.CLASS_NAME, "description").text,
        price=float(product.find_element(By.CLASS_NAME, "price").text[1:]),
        rating=len(product.find_elements(By.CLASS_NAME, "glyphicon-star")),
        num_of_reviews=int(
            product.find_element(
                By.CSS_SELECTOR, "div.ratings > p.pull-right"
            ).text.split()[0]
        ),
    )


def parser_for_page(driver: webdriver) -> list[Product]:
    products = []
    products_items = driver.find_elements(By.CLASS_NAME, "thumbnail")

    for products_item in products_items:
        product = get_single_product(products_item)
        products.append(product)

    return products


def write_file(csv_path: str, products: list[Product]) -> None:
    with open(csv_path, "w", newline="") as file:
        csv_writer = csv.writer(file)
        csv_writer.writerow(PRODUCT_FIELDS)
        csv_writer.writerows([astuple(product) for product in products])


def get_all_products() -> None:
    driver = get_driver(headless=False)
    driver.implicitly_wait(1)
    driver.get(HOME_URL)

    homepage_products = parser_for_page(driver)
    write_file("home.csv", homepage_products)

    categories = ("Computers", "Tablets", "Laptops", "Phones", "Touch")

    for category in categories:
        driver.find_element(By.LINK_TEXT, category).click()
        try:
            driver.find_element(By.ID, "closeCookieBanner").click()
        except NoSuchElementException:
            pass

        while True:
            try:
                time.sleep(0.1)
                driver.find_element(By.LINK_TEXT, "More").click()
            except NoSuchElementException:
                break

        driver.execute_script("window.scrollTo(0, 0);")
        products = parser_for_page(driver)
        write_file(f"{category.lower()}.csv", products)

    driver.quit()


if __name__ == "__main__":
    get_all_products()
