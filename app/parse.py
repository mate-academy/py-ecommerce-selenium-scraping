import csv
import types
from dataclasses import dataclass
from time import sleep
from typing import Optional, Type
from urllib.parse import urljoin

from selenium import webdriver
from selenium.common import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more")


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


PRODUCT_FIELD_NAMES = [
    "title", "description", "price", "rating", "num_of_reviews"
]


class WebDriverContext:
    def __enter__(self) -> webdriver.Chrome:
        self.driver = webdriver.Chrome()
        return self.driver

    def __exit__(self,
                 exc_type: Optional[Type[BaseException]],
                 exc_value: Optional[BaseException],
                 traceback: Optional[types.TracebackType]
                 ) -> None:
        self.driver.quit()


def get_single_product(driver: WebElement) -> Product:
    title = driver.find_element(By.CLASS_NAME, "title")
    description = driver.find_element(By.CLASS_NAME, "description")
    price = driver.find_element(By.CLASS_NAME, "price")
    rating = driver.find_elements(By.CSS_SELECTOR, ".ws-icon-star")
    num_of_reviews = driver.find_element(By.CLASS_NAME, "review-count")

    return Product(
        title=title.get_attribute("title"),
        description=description.text,
        price=float(price.text.replace("$", "", 1)),
        rating=len(rating),
        num_of_reviews=int(num_of_reviews.text.split()[0])
    )


def get_list_products(elements: list[WebElement]) -> [Product]:
    return [get_single_product(element) for element in elements]


def click_cookie_button(driver: webdriver) -> None:
    try:
        button = driver.find_element(By.CLASS_NAME, "acceptCookies")
        if button.is_displayed() and button.is_enabled():
            button.click()
    except NoSuchElementException:
        print("Cookie consent button not found or interactable")


def get_more_button(driver: webdriver) -> WebElement:
    return driver.find_element(
        By.CSS_SELECTOR,
        ".ecomerce-items-scroll-more"
    )


def scrape_sidebar(driver: webdriver, urls: [dict[str, str]]) -> None:
    sidebar = driver.find_element(By.ID, "side-menu")
    positions = sidebar.find_elements(By.CLASS_NAME, "nav-link")
    for element in positions:
        item = {element.text: urljoin(
            BASE_URL,
            element.get_attribute("href")),
        }
        if item not in urls:
            urls.append(item)


def scrape_page(
        driver: webdriver,
        url: str,
        urls: [dict[str, str]]
) -> [Product]:
    driver.get(url)
    click_cookie_button(driver)
    scrape_sidebar(driver, urls)
    while True:
        try:
            more_button = WebDriverWait(driver, 10).until(
                ec.element_to_be_clickable((
                    By.CSS_SELECTOR, ".ecomerce-items-scroll-more"
                ))
            )
            more_button.click()
            sleep(1)
        except TimeoutException:
            break
    products = driver.find_elements(By.CLASS_NAME, "product-wrapper")
    return get_list_products(products)


def write_to_csv(
        data: [Product],
        field_names: [str],
        path_file: str
) -> None:
    with open(path_file, "w", newline="", encoding="UTF-8") as file:
        writer = csv.writer(file)
        writer.writerow(field_names)
        for instance in data:
            row_data = [getattr(instance, field) for field in field_names]
            writer.writerow(row_data)


def get_all_products() -> None:
    urls = [{"Home": HOME_URL, }, ]
    with WebDriverContext() as driver:
        for url_dict in urls:
            for name, path in url_dict.items():
                products = scrape_page(driver, path, urls)
                file_name = f"{name.lower()}.csv"
                write_to_csv(products, PRODUCT_FIELD_NAMES, file_name)


if __name__ == "__main__":
    get_all_products()
