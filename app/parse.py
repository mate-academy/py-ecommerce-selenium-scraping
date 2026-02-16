import csv
from dataclasses import dataclass
from urllib.parse import urljoin

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


def create_driver() -> webdriver.Chrome:
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")  # optional task
    options.add_argument("--start-maximized")
    return webdriver.Chrome(options=options)


def accept_cookies(driver: webdriver.Chrome) -> None:
    try:
        cookie_btn = driver.find_element(By.ID, "cookie-accept")
        cookie_btn.click()
    except Exception:
        pass


def parse_single_page(driver: webdriver.Chrome, url: str) -> list[Product]:
    driver.get(url)
    accept_cookies(driver)

    WebDriverWait(driver, 5).until(
        EC.presence_of_element_located((By.CLASS_NAME, "thumbnail"))
    )

    products: list[Product] = []
    processed_count = 0

    while True:
        items = driver.find_elements(By.CLASS_NAME, "thumbnail")

        new_items = items[processed_count:]

        for item in new_items:
            title = item.find_element(By.CLASS_NAME, "title").get_attribute("title")
            description = item.find_element(By.CLASS_NAME, "description").text

            price_text = item.find_element(By.CLASS_NAME, "price").text
            price = float(price_text.replace("$", ""))

            rating = len(item.find_elements(By.CLASS_NAME, "glyphicon-star"))

            reviews_text = item.find_element(By.CLASS_NAME, "pull-right").text
            num_of_reviews = int(reviews_text.split()[0])

            products.append(
                Product(
                    title=title,
                    description=description,
                    price=price,
                    rating=rating,
                    num_of_reviews=num_of_reviews,
                )
            )

        processed_count = len(items)

        try:
            more_button = driver.find_element(By.CLASS_NAME, "btn-primary")
            more_button.click()

            WebDriverWait(driver, 5).until(
                lambda d: len(d.find_elements(By.CLASS_NAME, "thumbnail")) > processed_count
            )

        except Exception:
            break

    return products


def save_to_csv(filename: str, products: list[Product]) -> None:
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
    driver = create_driver()

    pages = {
        "home.csv": HOME_URL,
        "computers.csv": urljoin(BASE_URL, "test-sites/e-commerce/more/computers"),
        "laptops.csv": urljoin(BASE_URL, "test-sites/e-commerce/more/computers/laptops"),
        "tablets.csv": urljoin(BASE_URL, "test-sites/e-commerce/more/computers/tablets"),
        "phones.csv": urljoin(BASE_URL, "test-sites/e-commerce/more/phones"),
        "touch.csv": urljoin(BASE_URL, "test-sites/e-commerce/more/phones/touch"),
    }

    try:
        for filename, url in pages.items():
            products = parse_single_page(driver, url)
            save_to_csv(filename, products)
    finally:
        driver.quit()


if __name__ == "__main__":
    get_all_products()
