import csv
from dataclasses import dataclass, fields
from time import sleep
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from tqdm import tqdm

BASE_URL = "https://webscraper.io"

URLS = {
    "home": urljoin(BASE_URL, "test-sites/e-commerce/more"),
    "computers": urljoin(BASE_URL, "test-sites/e-commerce/more/computers"),
    "laptops": urljoin(
        BASE_URL, "test-sites/e-commerce/more/computers/laptops"
    ),
    "tablets": urljoin(
        BASE_URL, "test-sites/e-commerce/more/computers/tablets"
    ),
    "phones": urljoin(BASE_URL, "test-sites/e-commerce/more/phones"),
    "touch": urljoin(BASE_URL, "test-sites/e-commerce/more/phones/touch"),
}

CSV_PATHS = {
    "home_page_products": "home.csv",
    "computers_page_products": "computers.csv",
    "laptops_page_products": "laptops.csv",
    "tablets_page_products": "tablets.csv",
    "phones_page_products": "phones.csv",
    "touch_page_products": "touch.csv",
}

OPTIONS_CHROME = webdriver.ChromeOptions()
OPTIONS_CHROME.add_argument("--window-size=1920,1080")
OPTIONS_CHROME.add_argument("--headless")


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


def click_accept_cookies(driver: webdriver.Chrome) -> None:
    cookies = driver.find_elements(By.CLASS_NAME, "acceptContainer")

    if cookies:
        button = cookies[0].find_element(By.TAG_NAME, "button")
        WebDriverWait(driver, 1).until(ec.element_to_be_clickable(button))
        button.click()


def parse_single_products(soup: BeautifulSoup) -> Product:
    return Product(
        title=soup.select_one(".title").text,
        description=soup.select_one(".description").text,
        price=float(soup.select_one(".price").text.replace("$", "")),
        rating=len(soup.select(".ws-icon-star")),
        num_of_reviews=int(
            soup.select_one(".review-count").text.split(" ")[0]
        ),
    )


def get_single_page_products(page_soup: BeautifulSoup) -> list[Product]:
    products = page_soup.select(".product-wrapper")
    return [
        parse_single_products(product)
        for product in tqdm(products, desc="Parser products")
    ]


def click_all_button_more(driver: webdriver.Chrome) -> None:
    button = driver.find_elements(By.CLASS_NAME, "ecomerce-items-scroll-more")
    if button:
        button = button[0]
        while not button.get_attribute("style"):
            button.click()
            sleep(0.1)


def get_all_products() -> dict[str, list[Product]]:
    all_products = {}
    for key, url in URLS.items():
        with webdriver.Chrome(options=OPTIONS_CHROME) as driver:
            driver.get(url)
            click_accept_cookies(driver)
            click_all_button_more(driver)
            html = driver.page_source
            soup = BeautifulSoup(html, "html.parser")
            products = get_single_page_products(soup)
            all_products[key] = products

            csv_path = CSV_PATHS.get(f"{key}_page_products")
            write_products_to_csv(products, csv_path)

    return all_products


PRODUCT_FIELDS = [field.name for field in fields(Product)]


def write_products_to_csv(products: [Product], file_name: str) -> None:
    with open(file_name, "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(PRODUCT_FIELDS)
        for product in products:
            writer.writerow([
                product.title,
                product.description,
                product.price,
                product.rating,
                product.num_of_reviews,
            ])


if __name__ == "__main__":
    all_products = get_all_products()
    # for key, products in all_products.items():
    #     csv_path = CSV_PATHS.get(f"{key}_page_products")
    #     write_products_to_csv(products, csv_path)
