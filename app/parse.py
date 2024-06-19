import csv
import time
from dataclasses import dataclass, fields
from typing import List, Dict
from urllib.parse import urljoin
from selenium import webdriver
from selenium.common import NoSuchElementException
from selenium.webdriver.common.by import By

BASE_URL = "https://webscraper.io/test-sites/"
PAGE_URLS = {
    "home": urljoin(BASE_URL, "e-commerce/more/"),
    "computers": urljoin(BASE_URL, "e-commerce/more/computers"),
    "laptops": urljoin(BASE_URL, "e-commerce/more/computers/laptops"),
    "tablets": urljoin(BASE_URL, "e-commerce/more/computers/tablets"),
    "phones": urljoin(BASE_URL, "e-commerce/more/phones"),
    "touch": urljoin(BASE_URL, "e-commerce/more/phones/touch"),
}


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


PRODUCT_FIELDS = [field.name for field in fields(Product)]


def parse_products_on_page(driver: webdriver.Chrome, url: str) -> List[Product]:
    driver.get(url)
    accept_cookies_if_asked(driver)
    products = []
    while has_next_page(driver):
        navigate_to_next_page(driver)
    for product_element in driver.find_elements(By.CLASS_NAME, "thumbnail"):
        title = get_title(product_element)
        price = get_price(product_element)
        description = get_description(product_element)
        rating = get_rating(product_element)
        review_count = get_review_count(product_element)
        products.append(
            Product(
                title=title,
                description=description,
                price=price,
                rating=rating,
                num_of_reviews=review_count,
            )
        )
    return products


def get_title(product_element: webdriver.Chrome) -> str:
    return product_element.find_element(By.CLASS_NAME, "title").get_attribute("title")


def get_price(product_element: webdriver.Chrome) -> float:
    price_text = product_element.find_element(By.CLASS_NAME, "price").text
    return float(price_text.replace("$", ""))


def get_description(product_element: webdriver.Chrome) -> str:
    return product_element.find_element(By.CLASS_NAME, "description").text


def get_rating(product_element: webdriver.Chrome) -> int:
    return len(product_element.find_elements(By.CSS_SELECTOR, "p:nth-of-type(2) > span"))


def get_review_count(product: webdriver.Chrome) -> int:
    try:
        review_element = product.find_element(By.CLASS_NAME, "review-count")
        num_of_reviews = int(review_element.text.split()[0])
    except NoSuchElementException:
        num_of_reviews = 0
    return num_of_reviews


def accept_cookies_if_asked(driver: webdriver.Chrome) -> None:
    try:
        accept_cookies_button = driver.find_element(
            By.CLASS_NAME, "acceptCookies"
        )
        if accept_cookies_button.is_displayed():
            accept_cookies_button.click()
    except NoSuchElementException:
        pass


def has_next_page(driver: webdriver.Chrome) -> bool:
    try:
        next_button = driver.find_element(
            By.CLASS_NAME, "ecomerce-items-scroll-more"
        )
        return next_button.is_displayed()
    except NoSuchElementException:
        return False


def navigate_to_next_page(driver: webdriver.Chrome) -> bool:
    try:
        next_button = driver.find_element(
            By.CLASS_NAME, "ecomerce-items-scroll-more"
        )
        driver.execute_script("arguments[0].scrollIntoView();", next_button)
        next_button.click()
        time.sleep(0.5)
        return True
    except NoSuchElementException:
        return False


def scrape_products() -> Dict[str, List[Product]]:
    driver = webdriver.Chrome()
    try:
        products_data: dict[str, list[Product]] = {}
        for page_name, page_url in PAGE_URLS.items():
            products = parse_products_on_page(driver, page_url)
            products_data[page_name] = products
    finally:
        driver.quit()
    return products_data


def write_to_csv(products_data: Dict[str, List[Product]]) -> None:
    for page_name, products in products_data.items():
        output_csv_path = f"{page_name}.csv"
        with open(
                output_csv_path, "w", newline="", encoding="utf-8"
        ) as csvfile:
            writer = csv.DictWriter(
                csvfile,
                fieldnames=PRODUCT_FIELDS,
            )
            writer.writeheader()
            for product in products:
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
    products_data = scrape_products()
    write_to_csv(products_data)


if __name__ == "__main__":
    get_all_products()
