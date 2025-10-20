import csv
import time
from dataclasses import dataclass
from urllib.parse import urljoin

from selenium import webdriver
from selenium.common import NoSuchElementException
from selenium.webdriver.common.by import By


BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")
COMPUTERS_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/computers/")
LAPTOPS_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/computers/laptops")
TABLETS_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/computers/tablets")
PHONES_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/phones/")
TOUCH_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/phones/touch")


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


def get_product(url: str, page: str) -> None:
    driver = webdriver.Chrome()
    driver.get(url)

    while True:
        try:
            button = driver.find_element(
                By.CSS_SELECTOR,
                ".btn.btn-lg.btn-block.btn-primary.ecomerce-items-scroll-more",
            )
            if button.is_displayed():
                driver.execute_script("arguments[0].scrollIntoView(true);",
                                      button)
                driver.execute_script("arguments[0].click();",
                                      button)
                time.sleep(1)
            else:
                break
        except NoSuchElementException:
            break

    elements = driver.find_elements(By.CSS_SELECTOR,
                                    ".product-wrapper.card-body")
    scraped_elements = []

    for element in elements:
        title = element.find_element(By.CLASS_NAME, "title")
        description = element.find_element(By.CSS_SELECTOR,
                                           ".description.card-text")
        price = element.find_element(By.CSS_SELECTOR, ".price")
        rating = len(element.find_elements(By.CSS_SELECTOR, ".ws-icon-star"))
        num_of_reviews = element.find_element(
            By.CSS_SELECTOR, 'span[itemprop="reviewCount"]'
        )

        product = Product(
            title=title.get_attribute("title"),
            description=description.text,
            price=float(price.text.replace("$", "")),
            rating=rating,
            num_of_reviews=int(num_of_reviews.text.split()[0]),
        )
        scraped_elements.append(product)
    with open(f"{page}.csv", "w", newline="") as result_file:
        fieldnames = [
            "title",
            "description",
            "price",
            "rating",
            "num_of_reviews"
        ]
        writer = csv.DictWriter(result_file, fieldnames=fieldnames)

        writer.writeheader()
        for product in scraped_elements:
            writer.writerow(
                {
                    "title": product.title,
                    "description": product.description,
                    "price": product.price,
                    "rating": product.rating,
                    "num_of_reviews": product.num_of_reviews,
                }
            )


def get_all_products() -> None:
    get_product(HOME_URL, "home")
    get_product(COMPUTERS_URL, "computers")
    get_product(LAPTOPS_URL, "laptops")
    get_product(PHONES_URL, "phones")
    get_product(TABLETS_URL, "tablets")
    get_product(TOUCH_URL, "touch")


if __name__ == "__main__":
    get_all_products()
