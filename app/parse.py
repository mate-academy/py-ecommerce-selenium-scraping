import csv
from dataclasses import dataclass, fields, astuple
from urllib.parse import urljoin

from bs4 import BeautifulSoup, Tag
from selenium import webdriver
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException

# URLs
BASE_URL = "https://webscraper.io/test-sites/e-commerce/more/"
CATEGORIES = {
    "laptops": urljoin(BASE_URL, "computers/laptops"),
    "tablets": urljoin(BASE_URL, "computers/tablets"),
    "touch": urljoin(BASE_URL, "phones/touch"),
}


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


PRODUCT_FIELDS = [field.name for field in fields(Product)]


def parse_single_product(product: Tag) -> Product:
    ratings = product.select(
        ".ratings .ws-icon-star, .ratings .glyphicon-star"
    )
    rating = len(ratings)

    num_of_reviews = int(
        product.select_one(".ratings .pull-right").text.split()[0]
    )

    price = float(
        product.select_one(".price").text.replace("$", "")
    )
    description = product.select_one(
        ".description").text.strip().replace("\xa0", " "
                                             )

    title = product.select_one(".title")["title"]

    return Product(title, description, price, rating, num_of_reviews)


def click_more(driver: WebDriver) -> None:
    wait = WebDriverWait(driver, 5)

    while True:
        cards_before = len(
            driver.find_elements(By.CSS_SELECTOR, ".thumbnail")
        )

        try:
            more = driver.find_element(
                By.CSS_SELECTOR, ".ecomerce-items-scroll-more"
            )
            driver.execute_script("arguments[0].click();", more)

            wait.until(
                lambda d: len(
                    d.find_elements(By.CSS_SELECTOR, ".thumbnail")
                ) > cards_before
            )

        except TimeoutException:
            break
        except Exception:
            break


def write_csv(products: list[Product], filename: str) -> None:
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(PRODUCT_FIELDS)
        writer.writerows(astuple(p) for p in products)


def scrape_category(driver: WebDriver, name: str, url: str) -> None:
    driver.get(url)
    click_more(driver)

    soup = BeautifulSoup(driver.page_source, "html.parser")
    products = [parse_single_product(p) for p in soup.select(".thumbnail")]

    write_csv(products, f"{name}.csv")


def get_all_products(output_csv_path: str | None = None) -> None:
    with webdriver.Chrome() as driver:
        for name, url in CATEGORIES.items():
            scrape_category(driver, name, url)


if __name__ == "__main__":
    get_all_products()
