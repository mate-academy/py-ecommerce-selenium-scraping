import time
import csv
from dataclasses import dataclass
from urllib.parse import urljoin

from selenium import webdriver
from selenium.common import (
    NoSuchElementException,
    WebDriverException,
    TimeoutException
)
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")
COMPUTERS_URL = urljoin(HOME_URL, "computers")
LAPTOPS_URL = urljoin(HOME_URL, "computers/laptops")
TABLETS_URL = urljoin(HOME_URL, "computers/tablets")
PHONES_URL = urljoin(HOME_URL, "phones")
TOUCH_URL = urljoin(HOME_URL, "phones/touch")

DEFAULT_TIMEOUT = 2


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


def get_driver(headless: bool = False) -> webdriver.Chrome:
    options = webdriver.ChromeOptions()
    if headless:
        options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    return webdriver.Chrome(options=options)


def get_product_detail(
        driver: webdriver.Chrome,
        product_links: list
) -> list[Product]:
    product_data: list[Product] = []

    for link in product_links:
        driver.get(link)
        wait = WebDriverWait(driver, timeout=DEFAULT_TIMEOUT)
        try:
            product_name = wait.until(
                ec.presence_of_element_located(
                    (By.CSS_SELECTOR, "h4.title.card-title")
                )
            ).text.strip()
            product_description = driver.find_element(
                By.CSS_SELECTOR, "p.description.card-text"
            ).text.strip()
            product_num_of_reviews = int(
                driver.find_element(By.CSS_SELECTOR, "p.review-count")
                .text.strip()
                .split()[0]
            )
            product_rating = len(
                driver.find_elements(
                    By.CSS_SELECTOR,
                    "span.ws-icon.ws-icon-star"
                )
            )

            try:
                product_price = round(
                    float(
                        wait.until(
                            ec.presence_of_element_located(
                                (By.CSS_SELECTOR, "h4.price")
                            )
                        ).text.strip().replace("$", "")
                    ),
                    2,
                )
            except ValueError:
                print(f"Error parsing price for {product_name} at {link}")
                product_price = 0.0

            product_data.append(
                Product(
                    title=product_name,
                    description=product_description,
                    price=product_price,
                    rating=product_rating,
                    num_of_reviews=product_num_of_reviews,
                )
            )
        except (TimeoutException, NoSuchElementException) as e:
            print(e)
    return product_data


def scroll_and_load_all_products(driver: webdriver.Chrome, url: str) -> None:
    driver.get(url)
    wait = WebDriverWait(driver=driver, timeout=DEFAULT_TIMEOUT)
    try:
        cookie_button = wait.until(
            ec.element_to_be_clickable(
                (By.CSS_SELECTOR, "button.acceptCookies")
            )
        )
        cookie_button.click()
        time.sleep(0.1)
    except (TimeoutException, NoSuchElementException):
        pass

    while True:
        try:
            more_button = wait.until(
                ec.presence_of_element_located(
                    (By.CSS_SELECTOR, "a.ecomerce-items-scroll-more")
                )
            )
            driver.execute_script(
                "arguments[0].scrollIntoView();",
                more_button
            )
            time.sleep(0.1)
            more_button.click()
            time.sleep(0.1)
        except WebDriverException:
            break


def get_all_products_links(driver: webdriver.Chrome) -> list[str]:
    products_links = []
    try:
        WebDriverWait(driver=driver, timeout=DEFAULT_TIMEOUT).until(
            ec.presence_of_all_elements_located(
                (By.CSS_SELECTOR, "div.card.thumbnail")
            )
        )
        product_elements = driver.find_elements(
            By.CSS_SELECTOR, "div.card.thumbnail a.title"
        )
        for element in product_elements:
            product_link = element.get_attribute("href")
            if product_link:
                products_links.append(product_link)
    except (TimeoutException, NoSuchElementException):
        pass
    return products_links


def save_to_csv(filename: str, products: list[Product]) -> None:
    with open(filename, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(
            ["title", "description", "price", "rating", "num_of_reviews"]
        )
        for product in products:
            writer.writerow(
                [
                    product.title,
                    product.description,
                    product.price,
                    product.rating,
                    product.num_of_reviews,
                ]
            )


def get_all_products() -> None:
    pages = {
        "home.csv": HOME_URL,
        "computers.csv": COMPUTERS_URL,
        "laptops.csv": LAPTOPS_URL,
        "tablets.csv": TABLETS_URL,
        "phones.csv": PHONES_URL,
        "touch.csv": TOUCH_URL,
    }

    driver = get_driver(headless=True)

    for filename, url in pages.items():
        scroll_and_load_all_products(driver, url)
        links = get_all_products_links(driver)
        products = get_product_detail(driver, links)
        save_to_csv(filename, products)

    driver.quit()


if __name__ == "__main__":
    get_all_products()
