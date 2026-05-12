import csv
from dataclasses import dataclass, fields, astuple

from bs4 import BeautifulSoup, Tag
from selenium import webdriver
from selenium.common import TimeoutException
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait

BASE_URL = "https://webscraper.io/test-sites/e-commerce/more"

HOME_URL = BASE_URL
COMPUTERS_URL = f"{BASE_URL}/computers"
LAPTOPS_URL = f"{COMPUTERS_URL}/laptops"
TABLETS_URL = f"{COMPUTERS_URL}/tablets"
PHONES_URL = f"{BASE_URL}/phones"
TOUCH_URL = f"{PHONES_URL}/touch"

PAGES = [
    ("home.csv", HOME_URL),
    ("computers.csv", COMPUTERS_URL),
    ("laptops.csv", LAPTOPS_URL),
    ("tablets.csv", TABLETS_URL),
    ("phones.csv", PHONES_URL),
    ("touch.csv", TOUCH_URL),
]


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
        description=product.select_one(
            ".description"
        ).text.replace("\xa0", " "),
        price=float(product.select_one(".price").text.replace("$", "")),
        rating=len(product.select(".ws-icon-star")),
        num_of_reviews=int(
            product.select_one(".review-count").text.split()[0]
        ),
    )


def click_load_more_btn(driver: WebDriver) -> None:
    wait = WebDriverWait(driver, 10)

    while True:
        products_before = len(
            driver.find_elements(By.CSS_SELECTOR, ".card-body")
        )
        buttons = driver.find_elements(
            By.CLASS_NAME, "ecomerce-items-scroll-more"
        )

        if not buttons:
            break

        button = buttons[0]
        driver.execute_script("arguments[0].click();", button)

        try:
            wait.until(
                lambda d: len(d.find_elements(By.CSS_SELECTOR, ".card-body"))
                > products_before
            )
        except TimeoutException:
            break


def close_cookie_banner(driver: WebDriver) -> None:
    buttons = driver.find_elements(
        By.CSS_SELECTOR, "button[data-tid='banner-accept']"
    )

    if buttons:
        buttons[0].click()


def get_one_page_products(url: str) -> list[Product]:
    with webdriver.Chrome() as driver:
        driver.get(url)
        close_cookie_banner(driver)
        click_load_more_btn(driver)

        soup = BeautifulSoup(driver.page_source, features="html.parser")
        products = soup.select(".card-body")
        return [parse_single_product(product) for product in products]


def write_products_to_csv(filename: str, products: list[Product]) -> None:
    with open(filename, "w") as f:
        writer = csv.writer(f)
        writer.writerow(PRODUCT_FIELDS)
        writer.writerows([astuple(product) for product in products])


def get_all_products() -> None:
    for filename, url in PAGES:
        write_products_to_csv(filename, get_one_page_products(url))


if __name__ == "__main__":
    get_all_products()
