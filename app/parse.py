import csv
import time
from dataclasses import dataclass, astuple
from urllib.parse import urljoin

import tqdm
from selenium import webdriver
from selenium.common import NoSuchElementException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


BASE_URL = "https://webscraper.io/"
urls = {
    "home": "test-sites/e-commerce/more",
    "computers": "test-sites/e-commerce/more/computers",
    "laptops": "test-sites/e-commerce/more/computers/laptops",
    "tablets": "test-sites/e-commerce/more/computers/tablets",
    "phones": "test-sites/e-commerce/more/phones",
    "touch": "test-sites/e-commerce/more/phones/touch",
}


def make_url(url: str) -> str:
    return urljoin(BASE_URL, url)


def get_product(product: webdriver) -> Product:
    return Product(
        title=product.find_element(By.CLASS_NAME, "title").get_attribute(
            "title"
        ),
        description=product.find_element(By.CLASS_NAME, "description").text,
        price=float(product.find_element(By.CLASS_NAME, "price").text[1:]),
        rating=len(product.find_elements(By.CLASS_NAME, "ws-icon-star")),
        num_of_reviews=int(
            product.find_element(By.CLASS_NAME, "review-count").text.split()[0]
        ),
    )


def get_products(driver: webdriver) -> list[Product]:
    products = driver.find_elements(By.CLASS_NAME, "product-wrapper")
    return [get_product(product) for product in products]


def get_topic(url: str, driver: webdriver) -> list[Product]:
    driver.get(url)
    driver.maximize_window()

    try:
        button = driver.find_element(
            By.CLASS_NAME,
            "ecomerce-items-scroll-more"
        )
        while button.is_displayed():
            button.click()
            time.sleep(0.1)
    except NoSuchElementException:
        pass

    return get_products(driver)


def write_to_csv(products: list[Product], output_file: str) -> None:
    with open(output_file, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(
            ["title", "description", "price", "rating", "num_of_reviews"]
        )
        writer.writerows([astuple(product) for product in products])


def get_all_products() -> None:
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    driver = webdriver.Chrome(options=chrome_options)

    for topic, url in tqdm.tqdm(urls.items(), colour="green"):
        write_to_csv(get_topic(make_url(url), driver), topic + ".csv")

    driver.close()


if __name__ == "__main__":
    get_all_products()
