import csv
import time
from dataclasses import astuple, fields, dataclass
from pathlib import Path
from urllib.parse import urljoin

from selenium import webdriver
from selenium.common import TimeoutException, NoSuchElementException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


PAGES = {
    "home": HOME_URL,
    "computers": urljoin(HOME_URL, "computers"),
    "laptops": urljoin(HOME_URL, "computers/laptops"),
    "tablets": urljoin(HOME_URL, "computers/tablets"),
    "phones": urljoin(HOME_URL, "phones"),
    "touch": urljoin(HOME_URL, "phones/touch"),
}


def create_driver() -> webdriver.Chrome:
    options = Options()

    options.add_argument("--headless=new")

    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")

    return webdriver.Chrome(options=options)


def accept_cookies_if_present(driver: webdriver.Chrome) -> None:
    try:
        wait = WebDriverWait(driver, 3)

        accept_button = wait.until(
            EC.element_to_be_clickable(
                (
                    By.CSS_SELECTOR,
                    "button.acceptCookies, button#cookieBannerAccept, .acceptCookies",
                )
            )
        )

        accept_button.click()

    except TimeoutException:
        pass


def click_more_until_end(driver: webdriver.Chrome) -> None:
    wait = WebDriverWait(driver, 10)

    while True:
        try:
            products_before = len(driver.find_elements(By.CSS_SELECTOR, ".thumbnail"))

            more_button = wait.until(
                EC.element_to_be_clickable(
                    (By.CSS_SELECTOR, "a.ecomerce-items-scroll-more")
                )
            )

            driver.execute_script(
                "arguments[0].scrollIntoView({block: 'center'});",
                more_button,
            )

            time.sleep(0.3)
            more_button.click()

            wait.until(
                lambda current_driver: len(
                    current_driver.find_elements(By.CSS_SELECTOR, ".thumbnail")
                )
                > products_before
            )

        except TimeoutException:
            break

        except NoSuchElementException:
            break


def parse_product(product_card) -> Product:
    title_element = product_card.find_element(By.CLASS_NAME, "title")

    title = title_element.get_attribute("title")
    if not title:
        title = title_element.text

    description = product_card.find_element(By.CLASS_NAME, "description").text

    price_text = product_card.find_element(By.CLASS_NAME, "price").text
    price = float(price_text.replace("$", ""))

    rating_elements = product_card.find_elements(By.XPATH, ".//*[@data-rating]")

    if rating_elements:
        rating = int(rating_elements[0].get_attribute("data-rating"))
    else:
        rating = len(product_card.find_elements(By.CLASS_NAME, "ws-icon-star"))

    reviews_text = product_card.find_element(By.CLASS_NAME, "review-count").text
    num_of_reviews = int(reviews_text.split()[0])

    return Product(
        title=title,
        description=description,
        price=price,
        rating=rating,
        num_of_reviews=num_of_reviews,
    )


def parse_page(driver: webdriver.Chrome, url: str) -> list[Product]:
    driver.get(url)

    accept_cookies_if_present(driver)

    wait = WebDriverWait(driver, 10)
    wait.until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".thumbnail"))
    )

    click_more_until_end(driver)

    product_cards = driver.find_elements(By.CSS_SELECTOR, ".thumbnail")

    return [parse_product(product_card) for product_card in product_cards]


def write_products_to_csv(filename: str, products: list[Product]) -> None:
    with open(filename, "w", newline="", encoding="utf-8") as csv_file:
        writer = csv.writer(csv_file)

        writer.writerow([field.name for field in fields(Product)])

        for product in products:
            writer.writerow(astuple(product))


def get_all_products() -> None:
    driver = create_driver()

    try:
        for page_name, page_url in PAGES.items():
            products = parse_page(driver, page_url)
            write_products_to_csv(f"{page_name}.csv", products)

    finally:
        driver.quit()


if __name__ == "__main__":
    get_all_products()