import csv
import time
from dataclasses import dataclass
from urllib.parse import urljoin

from selenium import webdriver
from selenium.webdriver.common.by import By


BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")

file_names = {
    "https://webscraper.io/test-sites/e-commerce/more/phones": "phones",
    "https://webscraper.io/test-sites/e-commerce/more/computers": "computers",
    "https://webscraper.io/test-sites/e-commerce/more": "home",
}


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


def write_to_file(name: str, products: list[Product]) -> None:
    with open(f"{name}.csv", "w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(
            [
                "title", "description", "price", "rating", "num_of_reviews"
            ]
        )
        for product in products:
            writer.writerow([
                product.title,
                product.description,
                product.price,
                product.rating,
                product.num_of_reviews
            ])


def process_page(driver: webdriver, link: str, is_more: bool = True) -> None:
    driver.get(link)

    if is_more:
        header = driver.find_element(By.CLASS_NAME, "page-header")
        header = header.text.split(" / ")[1].lower()

        more_button = driver.find_element(
            By.CLASS_NAME,
            "ecomerce-items-scroll-more"
        )
        while more_button.is_displayed():
            more_button.click()
            time.sleep(0.5)
            more_button = driver.find_element(
                By.CLASS_NAME,
                "ecomerce-items-scroll-more"
            )
    else:
        header = file_names.get(link)

    products = driver.find_elements(By.CLASS_NAME, "card-body")

    goods = []
    for product in products:
        price = product.find_element(By.CLASS_NAME, "price").text.strip("$")
        title = product.find_element(
            By.CLASS_NAME, "title"
        ).get_property("title")
        description = product.find_element(By.CLASS_NAME, "description").text
        reviews = product.find_element(
            By.CLASS_NAME, "review-count"
        ).text.split()[0]
        stars = product.find_elements(By.CLASS_NAME, "ws-icon")
        goods.append(
            Product(
                title=title,
                description=description,
                price=float(price),
                rating=len(stars),
                num_of_reviews=int(reviews)
            )
        )
    write_to_file(header, goods)


def get_all_popular_products(driver: webdriver) -> None:
    pages = driver.find_element(By.CLASS_NAME, "sidebar-nav")
    pages = pages.find_elements(By.CLASS_NAME, "nav-link")
    pages = [page.get_property("href") for page in pages]
    for page_link in pages:
        process_page(driver, page_link, is_more=False)


def get_all_products() -> None:
    driver = webdriver.Firefox()
    driver.get(HOME_URL)

    get_all_popular_products(driver)

    categories = driver.find_elements(By.CLASS_NAME, "category-link")
    category_links = [cat.get_property("href") for cat in categories]

    for link in category_links:
        driver.get(link)
        subcategories = driver.find_elements(By.CLASS_NAME, "subcategory-link")
        subcategories_links = [
            sub.get_property("href") for sub in subcategories
        ]
        for sublink in subcategories_links:
            process_page(driver, sublink)
    driver.close()


if __name__ == "__main__":
    get_all_products()
