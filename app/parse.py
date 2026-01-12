from dataclasses import dataclass
from urllib.parse import urljoin
import csv
import re
import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException, ElementNotInteractableException, TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC



BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")


PAGES = {
    "home": HOME_URL,
    "computers": urljoin(BASE_URL, "test-sites/e-commerce/more/computers/"),
    "laptops": urljoin(BASE_URL, "test-sites/e-commerce/more/computers/laptops"),
    "tablets": urljoin(BASE_URL, "test-sites/e-commerce/more/computers/tablets"),
    "phones": urljoin(BASE_URL, "test-sites/e-commerce/more/phones"),
    "touch": urljoin(BASE_URL, "test-sites/e-commerce/more/phones/touch"),
}


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


def create_driver() -> webdriver.Chrome:
    options = Options()
    options.add_argument("--window-size=1920x1080")
    # options.add_argument("--headless")
    driver = webdriver.Chrome(options=options)
    driver.implicitly_wait(2)
    return driver


def accept_cookies_if_present(driver: webdriver.Chrome) -> None:
    try:
        button = driver.find_element(By.CSS_SELECTOR, "button.acceptCookies")
        button.click()
        time.sleep(0.3)
    except NoSuchElementException:
        return


def click_more_until_end(driver: webdriver.Chrome) -> None:
    while True:
        try:
            more_button = driver.find_element(By.CSS_SELECTOR, "a.ecomerce-items-scroll-more")
            if not more_button.is_displayed() or not more_button.is_enabled():
                break
            item_before = len(driver.find_elements(By.CSS_SELECTOR, "div.thumbnail"))
            more_button.click()
            try:

                WebDriverWait(driver, 5).until(
                    lambda d: len(d.find_elements(By.CSS_SELECTOR, "div.thumbnail")) > item_before
                )
            except TimeoutException:

                break
            time.sleep(0.2)
        except (NoSuchElementException, ElementNotInteractableException):
            break


def parse_price(text: str) -> float:
    cleaned = re.sub(r"[^0-9.]", "", text)
    return float(cleaned) if cleaned else 0.0


def parse_review(text: str) -> int:
    match = re.search(r"\d+", text)
    return int(match.group()) if match else 0


def parse_products_from_page(driver: webdriver.Chrome) -> list[Product]:
    products: list[Product] = []

    cards = driver.find_elements(By.CSS_SELECTOR, "div.thumbnail")
    for card in cards:
        # title
        title_element = card.find_element(By.CSS_SELECTOR, "a.title")
        title = title_element.get_attribute("title").strip() or title_element.text.strip()

        # description
        description = card.find_element(By.CSS_SELECTOR, "p.description").text.strip()

        # price
        try:
            price_text = card.find_element(
                By.CSS_SELECTOR, "span[itemprop='price']"
            ).text.strip()
        except NoSuchElementException:
            price_text = card.find_element(
                By.CSS_SELECTOR, "h4.price"
            ).text.strip()

        price = parse_price(price_text)

        # rating
        try:
            rating_element = card.find_element(By.CSS_SELECTOR, "p[data-rating]")
            rating = int(rating_element.get_attribute("data-rating"))
        except NoSuchElementException:
            stars = card.find_elements(
                By.CSS_SELECTOR,
                "span.glyphicon-star, span.ws-icon-star"
            )
            rating = len(stars)

        # num of reviews
        reviews_text = card.find_element(By.CSS_SELECTOR, "span[itemprop='reviewCount']").text.strip()
        num_of_reviews = parse_review(reviews_text)

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


def save_products_to_csv(filename: str, products: list[Product]) -> None:
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["title", "description", "price", "rating", "num_of_reviews"])

        for p in products:
            writer.writerow([p.title, p.description, p.price, p.rating, p.num_of_reviews])


def get_all_products() -> None:
    driver = create_driver()
    try:
        for page_name, url in PAGES.items():
            driver.get(url)
            accept_cookies_if_present(driver)

            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.thumbnail"))
            )

            click_more_until_end(driver)
            products = parse_products_from_page(driver)
            save_products_to_csv(f"{page_name}.csv", products)

    finally:
        driver.quit()


if __name__ == "__main__":
    get_all_products()
