import csv
from dataclasses import dataclass, astuple
from urllib.parse import urljoin

from selenium import webdriver
from selenium.common.exceptions import (
    NoSuchElementException,
    ElementNotInteractableException,
    ElementClickInterceptedException,
    TimeoutException
)
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.wait import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support import expected_conditions as ec


BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")
COMPUTERS_URL = urljoin(HOME_URL, "computers/")
LAPTOPS_URL = urljoin(COMPUTERS_URL, "laptops")
TABLETS_URL = urljoin(COMPUTERS_URL, "tablets")
PHONES_URL = urljoin(HOME_URL, "phones/")
TOUCH_URL = urljoin(PHONES_URL, "touch")
PRODUCT_FIELDS = [
    "title",
    "description",
    "price",
    "rating",
    "num_of_reviews",
]
FILE_COLLECTION = {
    "home.csv": HOME_URL,
    "computers.csv": COMPUTERS_URL,
    "laptops.csv": LAPTOPS_URL,
    "tablets.csv": TABLETS_URL,
    "phones.csv": PHONES_URL,
    "touch.csv": TOUCH_URL,
}


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


def create_product(card: WebElement) -> Product | None:
    try:
        title_element = card.find_element(By.CLASS_NAME, "title")

        try:
            rating_val = card.find_element(
                By.CSS_SELECTOR,
                "p[data-rating]"
            ).get_attribute(
                "data-rating")
            rating = int(rating_val)
        except NoSuchElementException:
            rating = len(card.find_elements(By.CLASS_NAME, "ws-icon-star"))

        try:
            reviews_text = card.find_element(By.CLASS_NAME,
                                             "review-count").text
            num_of_reviews = int(reviews_text.split()[0])
        except NoSuchElementException:
            num_of_reviews = 0

        product = Product(
            title=title_element.get_attribute("title"),
            description=card.find_element(By.CLASS_NAME,
                                          "description").text,
            price=float(
                card.find_element(
                    By.CLASS_NAME, "price"
                ).text.replace("$", "")),
            rating=rating,
            num_of_reviews=num_of_reviews
        )
        return product

    except Exception as e:
        print(f"Skipping a product due to error: {e}")


def scrap_single_page(driver: webdriver.Chrome, url: str) -> list[Product]:
    driver.get(url)
    wait = WebDriverWait(driver, 5)

    try:
        cookie_btn = driver.find_element(By.CLASS_NAME, "acceptCookies")
        cookie_btn.click()
    except NoSuchElementException:
        print(f"No cookies found on {url}")

    try:
        wait.until(
            ec.presence_of_element_located((By.CLASS_NAME, "card-body")))
    except (NoSuchElementException, TimeoutException):
        print(f"No products found on {url}")
        return []

    while True:
        try:
            current_count = len(
                driver.find_elements(By.CLASS_NAME, "card-body"))

            more_btn = wait.until(ec.element_to_be_clickable(
                (By.CLASS_NAME, "ecomerce-items-scroll-more")))

            if not more_btn.is_displayed():
                break

            driver.execute_script(
                "arguments[0].click();", more_btn
            )

            wait.until(lambda d: len(
                d.find_elements(By.CLASS_NAME, "card-body")) > current_count)

        except (
            NoSuchElementException,
            ElementNotInteractableException,
            ElementClickInterceptedException,
            TimeoutException,
        ):
            break

    product_cards = driver.find_elements(By.CLASS_NAME, "card-body")
    print(f"Finished loading {url}. Total items: {len(product_cards)}")

    products = (create_product(card) for card in product_cards)
    return [p for p in products if p]


def write_products_to_csv(products: list[Product], file_name: str) -> None:
    with open(file_name, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(PRODUCT_FIELDS)
        writer.writerows([astuple(product) for product in products])


def get_all_products() -> None:
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )

    try:
        for file_name, url in FILE_COLLECTION.items():
            write_products_to_csv(
                products=scrap_single_page(driver=driver, url=url),
                file_name=file_name
            )
    finally:
        driver.quit()


if __name__ == "__main__":
    get_all_products()
