import csv
import time
from dataclasses import dataclass, fields, astuple

from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup, Tag
from selenium.webdriver import Edge
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.service import Service

edge_driver_path = r"C:\WebDriver\msedgedriver.exe"
service = Service(edge_driver_path)
BASE_URL = "https://webscraper.io/"


URLS = {
    "HOME_URL" : urljoin(BASE_URL,
                         "test-sites/e-commerce/more/"),

    "COMPUTERS_URL" : urljoin(BASE_URL,
                              "test-sites/e-commerce/more/computers"),

    "LAPTOPS_URL" : urljoin(BASE_URL,
                            "test-sites/e-commerce/more/computers/laptops"),

    "TABLETS_URL" : urljoin(BASE_URL,
                            "test-sites/e-commerce/more/computers/tablets"),

    "PHONES_URL" : urljoin(BASE_URL,
                           "test-sites/e-commerce/more/phones"),

    "TOUCH_URL" : urljoin(BASE_URL,
                          "test-sites/e-commerce/more/phones/touch"),
}


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


PRODUCT_FIELDS = [field.name for field in fields(Product)]


def clean_invalid_text(value: str) -> str:
    """Replaces invalid characters, such as NBSP (\xa0), and trims spaces."""
    return value.replace("\xa0", " ").strip()


def parse_single_product(product: Tag, button: bool) -> Product:
    rating_element = product.select_one("p[data-rating]")
    if rating_element and "data-rating" in rating_element.attrs:
        product_rating = int(rating_element["data-rating"])
    else:

        product_rating = len(product.select("p span.ws-icon.ws-icon-star"))
    if button:
        pass
    else:
        return Product(
            title=product.select_one(".title")["title"],
            description=clean_invalid_text(
                product.select_one(".description").text
            ),
            price=float(product.select_one(".price").text.replace("$", "")),
            rating=product_rating,
            num_of_reviews=int(product.select_one(".review-count")
                               .text.split()[0])
        )


def write_product(page_name: str, products: list[Product]) -> None:
    name_file = page_name.lower().replace("_url", "")
    print(name_file)
    with open(f"{name_file}.csv", "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(PRODUCT_FIELDS)
        writer.writerows([astuple(product) for product in products])


def get_all_products() -> None:
    for page_name, page_url in URLS.items():
        results = []

        print(f"{page_name}: {page_url}")

        response = requests.get(page_url)
        soup = BeautifulSoup(response.text, "html.parser")
        products = soup.select(".product-wrapper")

        more_button = soup.select(".ecomerce-items-scroll-more")
        if more_button:
            driver = Edge(service=service)
            driver.get(page_url)
            while True:
                try:
                    driver.implicitly_wait(1)
                    button = driver.find_element(
                        By.CSS_SELECTOR, ".ecomerce-items-scroll-more")
                    if button.is_displayed():
                        button.click()
                        print("Click!!!")
                        time.sleep(1)
                    else:
                        print("No more displaible button stop clicking!!!")
                        soup = BeautifulSoup(driver.page_source, "html.parser")
                        products.extend(soup.select(".product-wrapper"))
                        driver.quit()
                        break
                except Exception as e:
                    print(f"Помилка при натисканні кнопки 'More': {e}")
                    break
        for product in products:
            results.append(parse_single_product(product, False))
        if results:
            write_product(page_name, results)


if __name__ == "__main__":
    get_all_products()
