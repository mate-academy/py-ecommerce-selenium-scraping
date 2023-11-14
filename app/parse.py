import csv
from dataclasses import dataclass, astuple, fields
from urllib.parse import urljoin

from bs4 import BeautifulSoup, Tag
from selenium import webdriver
from selenium.common import TimeoutException, ElementClickInterceptedException, \
    ElementNotInteractableException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")
URLS = {
    "home": HOME_URL,
    "computers": urljoin(HOME_URL, "computers"),
    "laptops": urljoin(HOME_URL, "computers/laptops"),
    "tablets": urljoin(HOME_URL, "computers/tablets"),
    "phones": urljoin(HOME_URL, "phones"),
    "touch": urljoin(HOME_URL, "phones/touch"),
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
    return Product(
        title=product.select_one(".title")["title"],
        description=product.select_one(".description").text,
        price=float(product.select_one(".price").text.replace("$", "")),
        rating=len(product.select(".ws-icon-star")),
        num_of_reviews=int(product.select_one(".review-count").text.split()[0])
    )


def parse_single_page(
        page_url: str, output_csv_path: str, driver: webdriver
) -> None:
    driver.get(page_url)
    wait = WebDriverWait(driver, 2)
    try:
        button = wait.until(
            EC.element_to_be_clickable(
                (By.ID, "closeCookieBanner")
            )
        )
        button.click()
    except TimeoutException:
        pass

    while True:
        try:
            button = wait.until(EC.presence_of_element_located(
                (By.CLASS_NAME, "ecomerce-items-scroll-more")
            ))
            button.click()
        except (TimeoutException, ElementClickInterceptedException, ElementNotInteractableException):
            break

    soup = BeautifulSoup(driver.page_source, "html.parser")

    products = []
    for product in soup.select(".card-body"):
        products.append(parse_single_product(product))

    write_data_to_csv(output_csv_path, products)


def get_all_products() -> None:
    with webdriver.Chrome() as driver:
        for page_name, url in URLS.items():
            parse_single_page(url, f"{page_name}.csv", driver)


def write_data_to_csv(output_csv_path: str, data: list) -> None:
    with open(output_csv_path, "w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(PRODUCT_FIELDS)
        writer.writerows([astuple(obj) for obj in data])


if __name__ == "__main__":
    get_all_products()
