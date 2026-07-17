import csv
from dataclasses import dataclass, astuple, fields
from urllib.parse import urljoin

from tqdm import tqdm

from selenium import webdriver
from selenium.common.exceptions import (
    ElementClickInterceptedException,
    NoSuchElementException,
    TimeoutException,
)
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.wait import WebDriverWait

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")

CARD_SELECTOR = ".card.thumbnail"

PAGES = {
    "home": HOME_URL,
    "computers": urljoin(HOME_URL, "computers"),
    "laptops": urljoin(HOME_URL, "computers/laptops"),
    "tablets": urljoin(HOME_URL, "computers/tablets"),
    "phones": urljoin(HOME_URL, "phones"),
    "touch": urljoin(HOME_URL, "phones/touch"),
}


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


def accept_cookies(driver: webdriver.Chrome, timeout: int = 1) -> None:
    try:
        cookie_btn = WebDriverWait(driver, timeout).until(
            ec.element_to_be_clickable(
                (By.CSS_SELECTOR,
                 "[data-tid='banner-accept'],"
                 " .t-acceptAllButton,"
                 " .acceptCookies")
            )
        )
        cookie_btn.click()
    except TimeoutException:
        pass


def click_more_button(driver: webdriver.Chrome) -> None:
    more_selector = "a.ecomerce-items-scroll-more"

    while True:
        try:
            more_btn = driver.find_element(
                By.CSS_SELECTOR, more_selector
            )
        except NoSuchElementException:
            break

        if not more_btn.is_displayed():
            break

        current_count = len(
            driver.find_elements(By.CSS_SELECTOR, CARD_SELECTOR)
        )

        try:
            more_btn.click()
        except ElementClickInterceptedException:
            driver.execute_script("arguments[0].click();", more_btn)

        try:
            WebDriverWait(driver, 10).until(
                lambda d: len(
                    d.find_elements(By.CSS_SELECTOR, CARD_SELECTOR)
                ) > current_count
            )
        except TimeoutException:
            break


def parse_card(card: WebElement) -> Product:
    title = card.find_element(
        By.CSS_SELECTOR, "a.title"
    ).get_attribute("title") or ""

    description = card.find_element(
        By.CSS_SELECTOR, "p.description"
    ).text

    price_text = card.find_element(
        By.CSS_SELECTOR, "h4.price"
    ).text
    price = float(price_text.removeprefix("$"))

    rating = len(
        card.find_elements(
            By.CSS_SELECTOR, ".ratings span.ws-icon-star"
        )
    )

    num_of_reviews = int(
        card.find_element(
            By.CSS_SELECTOR, "span[itemprop='reviewCount']"
        ).text
    )

    return Product(
        title=title,
        description=description,
        price=price,
        rating=rating,
        num_of_reviews=num_of_reviews,
    )


def parse_single_page(
    driver: webdriver.Chrome,
    url: str,
) -> list[Product]:
    driver.get(url)
    accept_cookies(driver)

    WebDriverWait(driver, 10).until(
        ec.presence_of_element_located(
            (By.CSS_SELECTOR, CARD_SELECTOR)
        )
    )

    click_more_button(driver)

    cards = driver.find_elements(By.CSS_SELECTOR, CARD_SELECTOR)

    return [parse_card(card) for card in cards]


def write_products_to_csv(
    products: list[Product],
    filename: str,
) -> None:
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([field.name for field in fields(Product)])
        for product in products:
            writer.writerow(astuple(product))


def get_all_products() -> None:
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--window-size=1920,1080")

    with webdriver.Chrome(options=options) as driver:
        driver.get(HOME_URL)
        accept_cookies(driver, timeout=10)

        for name, url in tqdm(PAGES.items(), desc="Scraping pages"):
            products = parse_single_page(driver, url)
            write_products_to_csv(products, f"{name}.csv")
            tqdm.write(f"{name}.csv: {len(products)} products scraped")


if __name__ == "__main__":
    get_all_products()
