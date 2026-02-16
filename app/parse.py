import csv
from dataclasses import dataclass
from urllib.parse import urljoin

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager


BASE_URL = "https://webscraper.io/test-sites/e-commerce/more/"


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


PAGES = {
    "home": "",
    "computers": "computers",
    "laptops": "computers/laptops",
    "tablets": "computers/tablets",
    "phones": "phones",
    "touch": "phones/touch",
}


def create_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    return webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options,
    )


def accept_cookies(driver):
    try:
        driver.find_element(By.ID, "cookie-accept").click()
    except Exception:
        pass


def parse_product(item):
    title = item.find_element(By.CLASS_NAME, "title").get_attribute("title")
    description = item.find_element(By.CLASS_NAME, "description").text
    price = float(item.find_element(By.CLASS_NAME, "price").text.replace("$", ""))

    reviews = int(
        item.find_element(By.CSS_SELECTOR, ".review-count [itemprop='reviewCount']")
        .text
    )

    rating = len(item.find_elements(By.CLASS_NAME, "ws-icon-star"))

    return Product(title, description, price, rating, reviews)


def parse_single_page(driver, url):
    driver.get(url)
    accept_cookies(driver)

    wait = WebDriverWait(driver, 5)
    wait.until(EC.presence_of_element_located((By.CLASS_NAME, "thumbnail")))

    products = []

    while True:
        items = driver.find_elements(By.CLASS_NAME, "thumbnail")

        for item in items[len(products):]:
            products.append(parse_product(item))

        try:
            more_btn = driver.find_element(By.CLASS_NAME, "btn-primary")
            more_btn.click()

            wait.until(
                lambda d: len(d.find_elements(By.CLASS_NAME, "thumbnail")) > len(products)
            )
        except Exception:
            break

    return products


def save_to_csv(filename, products):
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            ["title", "description", "price", "rating", "num_of_reviews"]
        )

        for p in products:
            writer.writerow(
                [p.title, p.description, p.price, p.rating, p.num_of_reviews]
            )


def get_all_products():
    driver = create_driver()

    try:
        for name, path in PAGES.items():
            url = urljoin(BASE_URL, path)
            products = parse_single_page(driver, url)
            save_to_csv(f"{name}.csv", products)
            print(f"Saved {name}.csv ({len(products)} products)")
    finally:
        driver.quit()


if __name__ == "__main__":
    get_all_products()
