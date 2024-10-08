import csv
from dataclasses import dataclass, fields, astuple
from time import sleep
from urllib.parse import urljoin
from tqdm import tqdm

from selenium import webdriver
from selenium.webdriver.common.by import By


BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")


URIS = {
    "home": "",
    "computers": "computers",
    "laptops": "computers/laptops",
    "tablets": "computers/tablets",
    "phones": "phones",
    "touch": "phones/touch",
}


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


PRODUCT_FIELDS = [field.name for field in fields(Product)]


def parse_page(driver: webdriver.Firefox, page_name: str) -> [Product]:
    elements = driver.find_elements(By.CLASS_NAME, "card")
    products = []

    print(f"Parsing {page_name} page: ")
    sleep(0.1)  # Fix for tqdm

    for element in tqdm(elements):
        title = element.find_element(By.CLASS_NAME, "title").get_attribute(
            "title"
        )
        description = element.find_element(By.CLASS_NAME, "description").text
        price = float(
            element.find_element(By.CLASS_NAME, "price").text.replace("$", "")
        )
        rating = len(element.find_elements(By.CLASS_NAME, "ws-icon-star"))
        num_of_reviews = int(
            element.find_element(By.CLASS_NAME, "review-count").text.split()[0]
        )
        products.append(
            Product(title, description, price, rating, num_of_reviews)
        )

    return products


def click_all_more(driver: webdriver.Firefox, uri: str) -> webdriver.Firefox:
    driver.get(urljoin(HOME_URL, uri))
    sleep(1)
    try:
        cookies_btn = driver.find_element(By.CLASS_NAME, "acceptCookies")
        cookies_btn.click()
    except Exception:
        pass

    try:
        more_btn = driver.find_element(
            By.CLASS_NAME, "ecomerce-items-scroll-more"
        )
        while more_btn.is_displayed():
            more_btn.click()

    except Exception:
        pass

    return driver


def write_to_csv(products: [Product], filename: str) -> None:
    with open(filename, "w") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(PRODUCT_FIELDS)
        writer.writerows([astuple(product) for product in products])


def get_all_products() -> None:
    options = webdriver.FirefoxOptions()
    options.add_argument("-headless")
    with webdriver.Firefox(options=options) as driver:

        for page_name, uri in URIS.items():
            page = click_all_more(driver, uri)
            products = parse_page(page, page_name)
            write_to_csv(products, f"{page_name}.csv")


if __name__ == "__main__":
    get_all_products()
