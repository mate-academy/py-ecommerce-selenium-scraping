import csv
import time
from dataclasses import dataclass, fields
from urllib.parse import urljoin

from bs4 import Tag, BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC  # noqa: N812

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "/test-sites/e-commerce/more")
COMPUTERS_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/computers")
LAPTOPS_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/computers/laptops")
TABLETS_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/computers/tablets")
PHONES_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/phones")
TOUCH_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/phones/touch")

_driver: WebDriver | None = None


def get_driver() -> WebDriver:
    return _driver


def set_driver(new_driver: WebDriver) -> None:
    global _driver
    _driver = new_driver


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


PRODUCT_FIELDS = [field.name for field in fields(Product)]


def parse_single_product(product: Tag) -> Product:
    star_spans = product.select("p span.ws-icon-star")
    rating = len(star_spans)
    return Product(
        title=product.select_one(".title")["title"].replace(
            "\xa0", " "
        ).strip(),
        description=product.select_one(
            ".description"
        ).text.replace("\xa0", " ").strip(),
        price=float(product.select_one(".price").text.replace("$", "")),
        rating=rating,
        num_of_reviews=int(product.select_one(".review-count").text.split()[0])
    )


def get_page_products(page_url: str) -> [Product]:
    driver = get_driver()
    driver.get(page_url)

    try:
        accept_button = driver.find_element(By.CLASS_NAME, "acceptCookies")
        accept_button.click()
    except Exception:
        pass

    while True:
        more_buttons = driver.find_elements(
            By.CLASS_NAME, "ecomerce-items-scroll-more"
        )
        if not more_buttons:
            break

        try:
            WebDriverWait(
                driver, 10
            ).until(
                EC.element_to_be_clickable(
                    (By.CLASS_NAME, "ecomerce-items-scroll-more")
                )
            )
            more_buttons[0].click()
            time.sleep(1)
        except Exception as e:
            print("Error clicking:", e)
            break

    page_source = driver.page_source
    soup = BeautifulSoup(page_source, "lxml")
    products = soup.select(".card-body")
    return [parse_single_product(product) for product in products]


def write_product_to_csv(file_name: str, products: [Product]) -> None:
    with open(file_name, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=PRODUCT_FIELDS)
        writer.writeheader()
        for product in products:
            writer.writerow({
                "title": product.title,
                "description": product.description,
                "price": product.price,
                "rating": product.rating,
                "num_of_reviews": product.num_of_reviews
            })


def get_all_products() -> None:
    with webdriver.Chrome() as driver:
        set_driver(driver)
        write_product_to_csv("home.csv", get_page_products(HOME_URL))
        write_product_to_csv("computers.csv", get_page_products(COMPUTERS_URL))
        write_product_to_csv("laptops.csv", get_page_products(LAPTOPS_URL))
        write_product_to_csv("tablets.csv", get_page_products(TABLETS_URL))
        write_product_to_csv("phones.csv", get_page_products(PHONES_URL))
        write_product_to_csv("touch.csv", get_page_products(TOUCH_URL))


if __name__ == "__main__":
    get_all_products()
