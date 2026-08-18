from dataclasses import dataclass
import csv
from urllib.parse import urljoin
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")

CONFIGS = [
    {"url": HOME_URL, "filename": "home.csv"},
    {"url": urljoin(BASE_URL, "test-sites/e-commerce/more/computers"), "filename": "computers.csv"},
    {"url": urljoin(BASE_URL, "test-sites/e-commerce/more/computers/laptops"), "filename": "laptops.csv"},
    {"url": urljoin(BASE_URL, "test-sites/e-commerce/more/computers/tablets"), "filename": "tablets.csv"},
    {"url": urljoin(BASE_URL, "test-sites/e-commerce/more/phones"), "filename": "phones.csv"},
    {"url": urljoin(BASE_URL, "test-sites/e-commerce/more/phones/touch"), "filename": "touch.csv"},
]


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


def parse_product(product_element) -> Product:
    title = product_element.find_element(By.CSS_SELECTOR, ".title").get_attribute("title")
    description = product_element.find_element(By.CSS_SELECTOR, ".description").text
    
    price_str = product_element.find_element(By.CSS_SELECTOR, ".price").text
    price = float(price_str.replace("$", ""))
    
    rating_elements = product_element.find_elements(By.CSS_SELECTOR, ".ratings .glyphicon-star")
    rating = len(rating_elements)
    
    reviews_str = product_element.find_element(By.CSS_SELECTOR, ".ratings .review-count").text
    num_of_reviews = int(reviews_str.split()[0])

    return Product(
        title=title,
        description=description,
        price=price,
        rating=rating,
        num_of_reviews=num_of_reviews,
    )


def accept_cookies(driver: webdriver.Chrome) -> None:
    try:
        accept_btn = WebDriverWait(driver, 3).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, ".acceptCookies, .cookie-accept, button.accept, .cc-accept"))
        )
        accept_btn.click()
    except TimeoutException:
        pass


def scrape_page(driver: webdriver.Chrome, url: str) -> list[Product]:
    driver.get(url)
    accept_cookies(driver)

    while True:
        try:
            more_button = WebDriverWait(driver, 3).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "a.btn.btn-primary.btn-lg.more-btn"))
            )
            if not more_button.is_displayed():
                break
            driver.execute_script("arguments[0].click();", more_button)
        except (TimeoutException, ElementClickInterceptedException):
            break

    WebDriverWait(driver, 5).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, ".thumbnail"))
    )
    product_elements = driver.find_elements(By.CSS_SELECTOR, ".thumbnail")
    return [parse_product(elem) for elem in product_elements]


def save_to_csv(products: list[Product], filename: str) -> None:
    with open(filename, mode="w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["title", "description", "price", "rating", "num_of_reviews"])
        for product in products:
            writer.writerow([
                product.title,
                product.description,
                product.price,
                product.rating,
                product.num_of_reviews
            ])


def get_all_products() -> None:
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")

    driver = webdriver.Chrome(options=options)
    try:
        for config in CONFIGS:
            products = scrape_page(driver, config["url"])
            save_to_csv(products, config["filename"])
    finally:
        driver.quit()


if __name__ == "__main__":
    get_all_products()

