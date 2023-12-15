import csv
from dataclasses import dataclass
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


def parse_single_product(product_soup: BeautifulSoup) -> Product:
    return Product(
        title=product_soup.select_one(".title")["title"],
        description=product_soup.select_one(
            "p.description"
        ).text.replace("\xa0", " "),
        price=float(product_soup.select_one(".price").text[1:]),
        rating=len(product_soup.select("span.ws-icon-star")),
        num_of_reviews=int(
            product_soup.select_one(".review-count").text.split()[0]
        ),
    )


def parse_all_products_from_page(url: str, driver: WebDriver) -> list[Product]:
    driver.get(url)

    try:
        more_button = driver.find_element(By.CLASS_NAME, "btn-primary")
    except Exception:
        more_button = None

    if more_button:
        while not more_button.get_property("style"):
            driver.execute_script("arguments[0].click();", more_button)

    soup = BeautifulSoup(driver.page_source, "html.parser")

    products_soup = soup.select(".thumbnail")
    result = [parse_single_product(ps) for ps in products_soup]

    return result


def write_products_to_csv(
        products: list[Product], csv_file_path: str
) -> None:
    with open(csv_file_path, "w", newline="") as csv_file:
        fieldnames = [
            "title",
            "description",
            "price",
            "rating",
            "num_of_reviews"
        ]
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)

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
    pages = {
        "home": HOME_URL,
        "phones": urljoin(HOME_URL, "phones"),
        "computers": urljoin(HOME_URL, "computers"),
        "touch": urljoin(HOME_URL, "phones/touch"),
        "tablets": urljoin(HOME_URL, "computers/tablets"),
        "laptops": urljoin(HOME_URL, "computers/laptops"),
    }
    for name, url in pages.items():
        driver = webdriver.Chrome()
        products = parse_all_products_from_page(url, driver)

        write_products_to_csv(products, f"{name}.csv")

        driver.close()


if __name__ == "__main__":
    get_all_products()
