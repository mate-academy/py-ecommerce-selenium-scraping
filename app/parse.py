import csv

from dataclasses import dataclass
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait

from selenium.common.exceptions import TimeoutException, NoSuchElementException

from urllib.parse import urljoin

from selenium import webdriver

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


def accept_cookies(driver: WebDriver) -> None:
    try:
        cookie_button = driver.find_element(By.ID, "cookie-accept")
        cookie_button.click()
    except NoSuchElementException:
        pass


def click_more_until_end(driver: WebDriver) -> None:
    wait = WebDriverWait(driver, 10)

    while True:
        products_before = len(
            driver.find_elements(
                By.CSS_SELECTOR, ".thumbnail"
            )
        )

        try:
            more_button = driver.find_element(
                By.CSS_SELECTOR, ".btn.btn-primary"
            )
        except NoSuchElementException:
            break

        if not more_button.is_displayed():
            break

        driver.execute_script(
            "arguments[0].click();", more_button
        )

        try:
            wait.until(
                lambda d: len(
                    d.find_elements(By.CSS_SELECTOR,
                                    ".thumbnail"
                                    )
                ) > products_before
            )
        except TimeoutException:

            break


def parse_products(driver: WebDriver) -> None:
    products = []

    cards = driver.find_elements(By.CSS_SELECTOR, ".thumbnail")

    for card in cards:

        title = card.find_element(
            By.CSS_SELECTOR, ".title"
        ).get_attribute("title")

        description = card.find_element(By.CSS_SELECTOR, ".description").text

        price_text = card.find_element(By.CSS_SELECTOR, ".price").text
        price = float(price_text.replace("$", ""))
        rating = len(
                card.find_elements(
                    By.CSS_SELECTOR,
                    ".ratings .ws-icon-star"
                )
            )

        reviews = card.find_elements(By.CSS_SELECTOR, "p.pull-right")
        num_of_reviews = int(reviews[0].text.split()[0]) if reviews else 0

        products.append(
            Product(
                title=title,
                description=description,
                price=price,
                rating=rating,
                num_of_reviews=num_of_reviews,
            )
        )

    return products


def get_all_products() -> None:
    driver = webdriver.Chrome()
    driver.implicitly_wait(5)

    pages = {
        "home": "",
        "computers": "computers",
        "laptops": "computers/laptops",
        "tablets": "computers/tablets",
        "phones": "phones",
        "touch": "phones/touch",
    }

    pages_with_more_button = {"laptops", "tablets", "touch"}

    try:
        for name, path in pages.items():
            url = urljoin(HOME_URL, path)
            driver.get(url)
            accept_cookies(driver)
            if name in pages_with_more_button:
                click_more_until_end(driver)

            products = parse_products(driver)
            save_to_csv(name, products)

    finally:
        driver.quit()


def save_to_csv(filename: str, products: list[Product]) -> None:
    with open(f"{filename}.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            ["title", "description", "price", "rating", "num_of_reviews"]
        )

        for product in products:
            writer.writerow(
                [
                    product.title,
                    product.description,
                    str(product.price),
                    product.rating,
                    product.num_of_reviews,
                ]
            )


if __name__ == "__main__":
    get_all_products()
