from selenium import webdriver
from selenium.common import NoSuchElementException
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from dataclasses import dataclass
from urllib.parse import urljoin
import csv
import time


BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


def accept_cookies(driver: WebDriver) -> None:
    try:
        accept_button = driver.find_element(
            By.CSS_SELECTOR,
            ".acceptContainer"
        )
        accept_button.click()
    except NoSuchElementException:
        pass


def scrape_products(driver: WebDriver, url: str) -> None:
    driver.get(url)
    accept_cookies(driver)
    WebDriverWait(driver, 10).until(
        ec.presence_of_element_located((By.CSS_SELECTOR, ".thumbnail"))
    )

    try:
        more_button = driver.find_elements(
            By.CSS_SELECTOR,
            ".ecomerce-items-scroll-more"
        )

        if more_button:
            more_button = more_button[0]
            while more_button.is_displayed():
                more_button.click()
                time.sleep(1)
    except Exception as e:
        print(f"No more 'More' buttons or encountered error: {e}")

    product_elements = driver.find_elements(By.CSS_SELECTOR, ".thumbnail")
    print(f"Total products found: {len(product_elements)}")

    products = []

    for product_element in product_elements:
        title = product_element.find_element(
            By.CLASS_NAME,
            "title"
        ).get_attribute("title")
        description = product_element.find_element(
            By.CSS_SELECTOR,
            ".description"
        ).text
        price = float(product_element.find_element(
            By.CSS_SELECTOR,
            ".price"
        ).text.replace("$", ""))
        rating = len(product_element.find_elements(
            By.CSS_SELECTOR,
            "p .ws-icon.ws-icon-star"
        ))
        num_of_reviews = int(
            product_element.find_element(
                By.CSS_SELECTOR,
                ".ratings"
            ).text.split()[0]
        )

        product = Product(title, description, price, rating, num_of_reviews)
        products.append(product)

    return products


def write_products_to_csv(filename: str, products: list) -> None:
    with open(filename, "w", newline="", encoding="utf-8") as file:
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
    driver = webdriver.Chrome()

    try:
        urls = [
            HOME_URL,
            urljoin(HOME_URL, "phones"),
            urljoin(HOME_URL, "phones/touch"),
            urljoin(HOME_URL, "computers"),
            urljoin(HOME_URL, "computers/tablets"),
            urljoin(HOME_URL, "computers/laptops"),
        ]

        for url in urls:
            try:
                products = scrape_products(driver, url)
                filename = url.split("/")[-1] + ".csv"
                if filename == ".csv":
                    filename = "home.csv"
                write_products_to_csv(filename, products)
            except Exception as e:
                print(f"Error scraping {url}: {e}")
    finally:
        driver.quit()


if __name__ == "__main__":
    get_all_products()
