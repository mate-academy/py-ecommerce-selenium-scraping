from dataclasses import dataclass
from urllib.parse import urljoin
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
import csv
import time

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


def setup_driver():
    options = Options()
    options.add_argument("--headless")
    driver = webdriver.Chrome(options=options)
    driver.implicitly_wait(5)
    return driver


def scrape_products(driver, page_url):
    driver.get(page_url)
    products = []

    while True:
        try:
            load_more_button = driver.find_element(
                By.CLASS_NAME, "btn.btn-primary.btn-block"
            )
            load_more_button.click()
            time.sleep(1)
        except NoSuchElementException:
            break

    product_elements = driver.find_elements(By.CLASS_NAME, "thumbnail")

    for product_element in product_elements:
        title = product_element.find_element(
            By.CLASS_NAME, "title"
        ).text
        description = product_element.find_element(
            By.CLASS_NAME, "description"
        ).text
        price = float(
            product_element.find_element(By.CLASS_NAME, "price").text.replace("$", "")
        )
        rating = len(
            product_element.find_elements(By.CLASS_NAME, "fa.fa-star")
        )
        num_of_reviews = int(
            product_element.find_element(By.CLASS_NAME, "ratings").text.split()[0]
        )

        products.append(Product(title, description, price, rating, num_of_reviews))

    return products


def save_to_csv(products, filename):
    with open(filename, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(
            [
                "Title",
                "Description",
                "Price",
                "Rating",
                "Number of Reviews"
            ]
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


def get_all_products():
    driver = setup_driver()

    try:
        pages = {
            "home": HOME_URL,
            "computers": urljoin(HOME_URL, "computers"),
            "laptops": urljoin(HOME_URL, "computers/laptops"),
            "tablets": urljoin(HOME_URL, "computers/tablets"),
            "phones": urljoin(HOME_URL, "phones"),
            "touch": urljoin(HOME_URL, "phones/touch")
        }

        for page_name, page_url in pages.items():
            products = scrape_products(driver, page_url)
            save_to_csv(products, f"{page_name}.csv")

    finally:
        driver.quit()


if __name__ == "__main__":
    get_all_products()
