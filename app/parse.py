import csv
from dataclasses import dataclass, asdict
from typing import Dict, List
from urllib.parse import urljoin
from selenium import webdriver
from selenium.common import TimeoutException, NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.remote.webelement import WebElement

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")
COMPUTERS_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/computers")
LAPTOPS_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/computers/laptops")
TABLETS_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/computers/tablets")
PHONES_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/phones")
TOUCH_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/phones/touch")
PAGES = {
    "home": HOME_URL,
    "computers": COMPUTERS_URL,
    "laptops": LAPTOPS_URL,
    "tablets": TABLETS_URL,
    "phones": PHONES_URL,
    "touch": TOUCH_URL,
}


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


def get_driver() -> webdriver.Chrome:
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--window-size=1920,1080")
    return webdriver.Chrome(options=options)


def parse_product(card: WebElement) -> Product:
    title = card.find_element(By.CSS_SELECTOR, ".title").get_attribute("title")
    description = card.find_element(By.CSS_SELECTOR, ".description").text
    price = float(
        card.find_element(
            By.CSS_SELECTOR, ".price"
        ).text.replace("$", "")
    )
    stars = card.find_elements(By.CSS_SELECTOR, ".ws-icon-star")
    rating = len(stars)
    try:
        reviews_element = card.find_element(
            By.CSS_SELECTOR, ".review-count"
        )
        num_of_reviews = int(reviews_element.text.split()[0])
    except (NoSuchElementException, IndexError, ValueError):
        num_of_reviews = 0
    return Product(
        title=title,
        description=description,
        price=price,
        rating=rating,
        num_of_reviews=num_of_reviews,
    )


def accept_cookies(driver: webdriver.Chrome) -> None:
    try:
        button = WebDriverWait(driver, 5).until(
            ec.element_to_be_clickable(
                (By.XPATH, "//button[contains(text(), 'Accept')]")
            )
        )
        button.click()
    except TimeoutException:
        pass


def load_all_products(driver: webdriver.Chrome) -> None:
    while True:
        buttons = driver.find_elements(
            By.CSS_SELECTOR, ".ecomerce-items-scroll-more"
        )
        if not buttons:
            break
        button = buttons[0]
        cards_before = len(
            driver.find_elements(By.CSS_SELECTOR, ".card-body")
        )
        driver.execute_script(
            "arguments[0].scrollIntoView(true);", button
        )
        driver.execute_script(
            "arguments[0].click();", button
        )
        try:
            WebDriverWait(driver, 10).until(
                lambda d: len(d.find_elements(
                    By.CSS_SELECTOR, ".card-body")
                ) > cards_before
            )
        except TimeoutException:
            break


def get_all_products() -> Dict[str, List[Product]]:
    driver = get_driver()
    all_data = {}

    for name, url in PAGES.items():
        driver.get(url)
        accept_cookies(driver)
        load_all_products(driver)

        WebDriverWait(driver, 10).until(
            ec.presence_of_all_elements_located((
                By.CSS_SELECTOR, ".card-body"
            ))
        )
        cards = driver.find_elements(By.CSS_SELECTOR, ".card-body")
        products = [parse_product(card) for card in cards]
        all_data[name] = products

    for name, products in all_data.items():
        write_products_to_csv(f"{name}.csv", products)

    driver.quit()
    return all_data


def write_products_to_csv(file_name: str, products: List[Product]) -> None:
    with open(file_name, "w") as f:
        writer = csv.DictWriter(f, fieldnames=asdict(products[0]).keys())
        writer.writeheader()
        writer.writerows([asdict(product) for product in products])


def main() -> None:
    get_all_products()


if __name__ == "__main__":
    main()
