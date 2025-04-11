import csv
import dataclasses
import time
from dataclasses import dataclass

from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from urllib.parse import urljoin

from selenium import webdriver
from selenium.common import NoSuchElementException, TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")
PAGES = {
    "home": HOME_URL,
    "computers": f"{HOME_URL}computers",
    "laptops": f"{HOME_URL}computers/laptops",
    "tablets": f"{HOME_URL}computers/tablets",
    "phones": f"{HOME_URL}phones",
    "touch": f"{HOME_URL}phones/touch",
}


# driver settings
def get_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-gpu")
    return webdriver.Chrome(service=Service(), options=options)


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


def parse_single_product(card: WebElement) -> Product:
    title = card.find_element(By.CSS_SELECTOR, "a.title").text.strip()
    description = card.find_element(By.CSS_SELECTOR, ".description").text.strip()
    price = float(card.find_element(By.CSS_SELECTOR, "h4.price").text.replace("$", ""))
    rating = len(card.find_elements(By.CSS_SELECTOR, ".ratings .rating span.ws-icon-star"))

    review_text = card.find_element(By.CSS_SELECTOR, ".ratings p").text
    reviews = int(review_text.strip().split(" ")[0])
    return Product(title, description, price, rating, reviews)


def click_more_until_end(driver: webdriver.Chrome):
    while True:
        try:
            more_btn = driver.find_element(By.CSS_SELECTOR, "a.btn.btn-primary")
            previous_count = len(driver.find_elements(By.CSS_SELECTOR, ".thumbnail"))
            driver.execute_script("arguments[0].click();", more_btn)
            WebDriverWait(driver, 10).until(
                lambda d: len(d.find_elements(By.CSS_SELECTOR, ".thumbnail")) > previous_count
            )
        except (NoSuchElementException, TimeoutException):
            break


def parse_page(driver):
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".thumbnail")))
    cards = driver.find_elements(By.CSS_SELECTOR, ".thumbnail")
    return [parse_single_product(card) for card in cards]


def write_to_csv(filename: str, products: [Product]):
    with open(filename, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([field.name for field in dataclasses.fields(Product)])
        writer.writerows([dataclasses.astuple(p) for p in products])


def get_all_products() -> None:
    driver = get_driver()
    for name, url in PAGES.items():
        print(f"Parsing {name}")
        driver.get(url)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".thumbnail"))
        )

        click_more_until_end(driver)

        products = parse_page(driver)

        write_to_csv(f"{name}.csv", products)
    driver.quit()


if __name__ == "__main__":
    get_all_products()
