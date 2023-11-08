import csv
from dataclasses import dataclass, astuple
from urllib.parse import urljoin

from selenium import webdriver
from selenium.common import (
    TimeoutException,
    ElementNotInteractableException,
    ElementClickInterceptedException,
)
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from tqdm import tqdm

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")
PAGES = {
    "home": HOME_URL,
    "phones": urljoin(HOME_URL, "phones/"),
    "touch": urljoin(HOME_URL, "phones/touch"),
    "computers": urljoin(HOME_URL, "computers/"),
    "laptops": urljoin(HOME_URL, "computers/laptops"),
    "tablets": urljoin(HOME_URL, "computers/tablets"),
}


class WebDriverSingleton:
    instance = None

    @classmethod
    def get_instance(cls) -> WebDriver:
        if cls.instance is None:
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--disable-gpu")
            cls.instance = webdriver.Chrome(options=chrome_options)
        return cls.instance

    @classmethod
    def close_driver(cls) -> None:
        if cls.instance:
            cls.instance.quit()
            cls.instance = None


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


def accept_cookies(driver: webdriver.Chrome) -> None:
    try:
        accept_button = WebDriverWait(driver, 3).until(
            EC.element_to_be_clickable((By.CLASS_NAME, "acceptCookies"))
        )
        accept_button.click()
    except TimeoutException:
        pass


def click_more_button(driver) -> None:
    try:
        button_more = driver.find_element(
            By.CLASS_NAME, "ecomerce-items-scroll-more"
        )
        while button_more and button_more.is_displayed():
            button_more.click()
    except ElementNotInteractableException:
        pass
    except ElementClickInterceptedException:
        pass


def parse_page(driver) -> list[Product]:
    product_elements = driver.find_elements(By.CSS_SELECTOR, ".thumbnail")
    products = []
    for element in product_elements:
        title = element.find_element(
            By.CSS_SELECTOR, ".title"
        ).get_attribute("title")

        description = element.find_element(
            By.CSS_SELECTOR, ".description"
        ).text

        price = float(element.find_element(
            By.CSS_SELECTOR, ".price"
        ).text.replace("$", ""))

        rating = int(len(element.find_elements(
            By.CSS_SELECTOR,
            ".ws-icon-star"
        )))

        num_of_reviews = int(element.find_element(
            By.CSS_SELECTOR,
            ".review-count"
        ).text.split()[0])

        products.append(
            Product(title, description, price, rating, num_of_reviews)
        )

    return products


def write_to_csv(products, csv_filename) -> None:
    with open(csv_filename, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(
            ["title", "description", "price", "rating", "num_of_reviews"]
        )
        writer.writerows(
            [astuple(quote) for quote in tqdm(
                products, desc=f"Writing to {csv_filename}"
            )]
        )


def get_all_products() -> None:
    driver = WebDriverSingleton.get_instance()

    for category, url in tqdm(
            PAGES.items(), desc="Visiting pages", unit="page"
    ):
        driver.get(url)
        accept_cookies(driver)
        if category in ["laptops", "tablets", "touch"]:
            click_more_button(driver)
        products = parse_page(driver)

        write_to_csv(products=products, csv_filename=f"{category}.csv")

    WebDriverSingleton.close_driver()


if __name__ == "__main__":
    get_all_products()
