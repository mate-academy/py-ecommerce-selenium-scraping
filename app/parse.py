from dataclasses import dataclass, fields, astuple
from urllib.parse import urljoin
import csv

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.common import (
    NoSuchElementException,
    StaleElementReferenceException,
    TimeoutException,
)


BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


FIELDS = [field.name for field in fields(Product)]


def get_all_links(driver: webdriver.Chrome) -> dict[str, str]:
    driver.get(HOME_URL)
    urls_dict = {"home": HOME_URL}

    menu_items_count = len(
        driver.find_elements(By.CSS_SELECTOR, "#side-menu .category-link")
    )
    for i in range(menu_items_count):
        current_links = driver.find_elements(
            By.CSS_SELECTOR, "#side-menu .category-link"
        )

        url = current_links[i].get_attribute("href")
        urls_dict[current_links[i].text.lower()] = url
        driver.execute_script("arguments[0].click();", current_links[i])
        child_urls = driver.find_elements(By.CSS_SELECTOR, ".subcategory-link")
        for url in child_urls:
            urls_dict[url.text.lower()] = url.get_attribute("href")
    return urls_dict


def parse_item(card: WebElement) -> Product:
    title = card.find_element(By.CSS_SELECTOR, ".title").get_attribute("title")
    description = card.find_element(By.CSS_SELECTOR, ".description").text
    price = float(card.find_element(
        By.CSS_SELECTOR, ".price"
    ).text.replace("$", ""))
    rating = len(card.find_elements(By.CSS_SELECTOR, ".ws-icon"))
    num_of_reviews = int(
        card.find_element(By.CSS_SELECTOR, ".review-count").text.split()[0]
    )
    return Product(title, description, price, rating, num_of_reviews)


def parse_page(driver: webdriver.Chrome, url: str) -> list[Product]:
    products = []
    driver.get(url)

    wait = WebDriverWait(driver, 2)
    while True:
        try:
            more = wait.until(
                ec.element_to_be_clickable(
                    (By.CSS_SELECTOR, ".ecomerce-items-scroll-more")
                )
            )
            driver.execute_script("arguments[0].click();", more)
        except (NoSuchElementException, TimeoutException):
            break
        except StaleElementReferenceException:
            continue

    cards = driver.find_elements(By.CSS_SELECTOR, ".card.thumbnail")
    for card in cards:
        products.append(parse_item(card))
    return products


def write_to_csv(filename: str, items: list[Product]) -> None:
    with open(f"{filename}.csv", "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(FIELDS)
        for item in items:
            writer.writerow(astuple(item))


def get_all_products() -> None:
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    driver = webdriver.Chrome(options=options)

    urls_with_names = get_all_links(driver)
    for filename, url in urls_with_names.items():
        items = parse_page(driver, url)
        write_to_csv(filename, items)
    driver.quit()


if __name__ == "__main__":
    get_all_products()
