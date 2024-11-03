from selenium import webdriver
from selenium.common import (
    TimeoutException,
    NoSuchElementException,
    ElementNotInteractableException
)
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from dataclasses import dataclass
import csv
from typing import List
import concurrent.futures

BASE_URL = "https://webscraper.io/"
HOME_URL = BASE_URL + "test-sites/e-commerce/more/"
URLS = {
    "home": HOME_URL,
    "computers": HOME_URL + "computers",
    "laptops": HOME_URL + "computers/laptops",
    "tablets": HOME_URL + "computers/tablets",
    "phones": HOME_URL + "phones",
    "touch": HOME_URL + "phones/touch",
}


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


def init_driver() -> webdriver.Chrome:
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(
        service=ChromeService(ChromeDriverManager().install()), options=options
    )
    return driver


def accept_cookies(driver: webdriver.Chrome) -> None:
    try:
        accept_button = WebDriverWait(driver, 2).until(
            ec.element_to_be_clickable((By.CLASS_NAME, "acceptCookies"))
        )
        accept_button.click()
        print("Cookies accepted")
    except (TimeoutException, NoSuchElementException) as e:
        print(f"Cookies not accepted: {e}")


def load_all_products(driver: webdriver.Chrome) -> None:
    while True:
        try:
            more_button = WebDriverWait(driver, 2).until(
                ec.presence_of_element_located(
                    (By.CLASS_NAME, "ecomerce-items-scroll-more")
                )
            )

            if (
                "disabled" not in more_button.get_attribute("class")
                and more_button.is_displayed()
            ):
                more_button.click()
                print("Clicked 'More' button")
            else:
                print("'More' button is either disabled or not displayed")
                break
        except (NoSuchElementException, ElementNotInteractableException) as e:
            print("The 'More' button was not found or became unavailable:", e)
            break


def scrape_page_products(driver: webdriver.Chrome) -> List[Product]:
    products = []
    product_elements = driver.find_elements(By.CLASS_NAME, "thumbnail")

    for product in product_elements:
        try:
            title = (
                product.find_element(By.CLASS_NAME, "title")
                .get_attribute("title")
                .strip()
            )
            description = product.find_element(
                By.CLASS_NAME, "description"
            ).text.strip()
            price = float(
                product.find_element(By.CLASS_NAME, "price")
                .text.strip()
                .replace("$", "")
            )
            rating = len(product.find_elements(By.CLASS_NAME, "ws-icon-star"))
            num_of_reviews = int(
                product.find_element(By.CLASS_NAME, "ratings").text.split()[0]
            )

            products.append(Product(
                title,
                description,
                price, rating,
                num_of_reviews)
            )
        except Exception as e:
            print(f"Error scraping product: {e}")

    return products


def scrape_category(url: str) -> List[Product]:
    driver = init_driver()
    driver.get(url)
    accept_cookies(driver)
    load_all_products(driver)
    products = scrape_page_products(driver)
    driver.quit()
    return products


def save_to_csv(products: List[Product], filename: str) -> None:
    with open(filename, "w", newline="", encoding="utf-8") as csvfile:
        fieldnames = [
            "title",
            "description",
            "price",
            "rating",
            "num_of_reviews"
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for product in products:
            writer.writerow(product.__dict__)


def get_all_products() -> None:
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_to_category = {
            executor.submit(scrape_category, url): category
            for category, url in URLS.items()
        }
        for future in concurrent.futures.as_completed(future_to_category):
            category = future_to_category[future]
            try:
                products = future.result()
                save_to_csv(products, f"{category}.csv")
            except (NoSuchElementException, ValueError) as e:
                print(f"Error retrieving products for {category}: {e}")


if __name__ == "__main__":
    get_all_products()
