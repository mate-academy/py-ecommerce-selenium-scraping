import csv
import time
from dataclasses import dataclass, fields, astuple, field
from selenium import webdriver
from selenium.common.exceptions import (
    NoSuchElementException,
    StaleElementReferenceException,
    ElementClickInterceptedException)
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from urllib.parse import urljoin

from bs4 import BeautifulSoup, Tag

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")
COMPUTERS_URL = urljoin(HOME_URL, "computers/")
LAPTOPS_URL = urljoin(COMPUTERS_URL, "laptops")
PHONES_URL = urljoin(HOME_URL, "phones/")
TABLETS_URL = urljoin(COMPUTERS_URL, "tablets")
TOUCH_URL = urljoin(PHONES_URL, "touch")


PAGES_TO_SCRAPE = {
    "home": HOME_URL,
    "computers": COMPUTERS_URL,
    "laptops": LAPTOPS_URL,
    "tablets": TABLETS_URL,
    "phones": PHONES_URL,
    "touch": TOUCH_URL
}


_driver: WebDriver | None = None


def get_driver() -> WebDriver:
    return _driver


def set_driver(new_driver: WebDriver) -> None:
    global _driver
    _driver = new_driver


def accept_cookies(driver: WebDriver):
    try:
        cookie_btn = driver.find_element(By.CLASS_NAME, "acceptCookies")
        if cookie_btn.is_displayed():
            cookie_btn.click()
            time.sleep(0.5)
    except NoSuchElementException:
        pass


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int
    additional_info: dict = field(default_factory=dict)


PRODUCT_FIELDS = [field.name for field in fields(Product)]


def parse_hdd_block_prices(product_soup: Tag) -> dict[str, float]:
    absolute_url = urljoin(BASE_URL, product_soup.select_one(".title")["href"])
    driver = get_driver()
    driver.get(absolute_url)

    prices = {}
    try:
        swatches = driver.find_element(By.CLASS_NAME, "swatches")
        buttons = swatches.find_elements(By.TAG_NAME, "button")

        for button in buttons:
            if not button.get_property("disabled"):
                old_price = driver.find_element(By.CLASS_NAME, "price").text
                button.click()
                try:
                    WebDriverWait(driver, 2).until(
                        lambda d: d.find_element(By.CLASS_NAME, "price").text != old_price
                    )
                except:
                    pass

                new_price = driver.find_element(By.CLASS_NAME, "price").text
                prices[button.get_property("value")] = float(new_price.replace("$", ""))

    except NoSuchElementException:
        pass

    return prices

def parse_single_product(product: Tag) -> Product:
    hdd_prices = parse_hdd_block_prices(product)

    rating = len(product.select(".ws-icon-star"))

    reviews_element = product.select_one(".review-count")
    num_of_reviews = int(reviews_element.text.split()[0]) if reviews_element else 0

    price_element = product.select_one(".price")
    price = float(price_element.text.replace("$", "")) if price_element else 0.0

    description = product.select_one(".description").text

    title_element = product.select_one(".title")
    title = title_element["title"] if title_element else "No Title"

    return Product(
        title=title,
        description=description,
        price=price,
        rating=rating,
        num_of_reviews=num_of_reviews,
        additional_info={"hdd_prices": hdd_prices},
    )


def process_pagination(driver: WebDriver):
    while True:
        try:
            more_btn = driver.find_element(By.CSS_SELECTOR, ".ecomerce-items-scroll-more")

            if not more_btn.is_displayed():
                break

            more_btn.click()
            time.sleep(1.5)

        except (NoSuchElementException,
                StaleElementReferenceException,
                ElementClickInterceptedException):
            break


def write_products_to_csv(products: [Product], name: str) -> None:
    file_name = f"{name}.csv"
    with open(file_name, "w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(PRODUCT_FIELDS)
        writer.writerows([astuple(product) for product in products])



def scrape_category_page(category_name: str, url: str):
    print(f"Start scraping category: {category_name}...")
    driver = get_driver()
    driver.get(url)
    accept_cookies(driver)
    process_pagination(driver)
    soup = BeautifulSoup(driver.page_source, "html.parser")

    product_tags = soup.select(".thumbnail")
    print(f"Found {len(product_tags)} products in {category_name}. Parsing details...")

    products = []
    for tag in product_tags:
        products.append(parse_single_product(tag))

    write_products_to_csv(products, category_name)
    print(f"Finished {category_name}. Saved to {category_name}.csv")


def get_all_products() -> None:
    with webdriver.Chrome() as driver:
        set_driver(driver)
        driver.maximize_window()

        for name, url in PAGES_TO_SCRAPE.items():
            scrape_category_page(name, url)


if __name__ == "__main__":
    get_all_products()
