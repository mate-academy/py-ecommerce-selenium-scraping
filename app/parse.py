import csv
from dataclasses import dataclass, fields, astuple
from urllib.parse import urljoin
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait


BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")
PAGES = {
    "home": HOME_URL,
    "computers": urljoin(HOME_URL, "computers"),
    "laptops": urljoin(HOME_URL, "computers/laptops"),
    "tablets": urljoin(HOME_URL, "computers/tablets"),
    "phones": urljoin(HOME_URL, "phones"),
    "touch": urljoin(HOME_URL, "phones/touch")
}


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


FIELDS = [field.name for field in fields(Product)]


def write_to_csv(products: list[Product], filename: str) -> None:
    with open(filename, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(FIELDS)
        writer.writerows([astuple(product) for product in products])


def get_products_from_page(driver: WebDriver, url: str) -> list[Product]:
    driver.get(url)
    wait = WebDriverWait(driver, 10)
    product = (By.CSS_SELECTOR, ".thumbnail")
    more_button = (By.CSS_SELECTOR, ".ecomerce-items-scroll-more")

    try:
        cookie_button = WebDriverWait(driver, 3).until(
            ec.element_to_be_clickable(
                (By.CSS_SELECTOR, "[data-tid='banner-accept']")
            )
        )
        cookie_button.click()
        wait.until(ec.invisibility_of_element(cookie_button))
    except TimeoutException:
        pass

    wait.until(ec.presence_of_all_elements_located(product))

    while True:
        more_buttons = driver.find_elements(*more_button)
        if not more_buttons or not more_buttons[0].is_displayed():
            break

        previous_count = len(driver.find_elements(*product))
        wait.until(ec.element_to_be_clickable(more_button)).click()
        wait.until(
            lambda browser: len(browser.find_elements(*product))
            > previous_count
        )

    products = []
    for card in driver.find_elements(*product):
        title = card.find_element(By.CSS_SELECTOR, ".title")
        description = card.find_element(By.CSS_SELECTOR, ".description")
        price = card.find_element(By.CSS_SELECTOR, ".price")
        reviews = card.find_element(By.CSS_SELECTOR, ".review-count")
        stars = card.find_elements(By.CSS_SELECTOR, ".ws-icon-star")

        products.append(
            Product(
                title=title.get_attribute("title") or title.text,
                description=description.text,
                price=float(price.text.replace("$", "")),
                rating=len(stars),
                num_of_reviews=int(reviews.text.split()[0]),
            )
        )

    return products


def get_all_products() -> None:
    with webdriver.Chrome() as driver:
        for product_type, url in PAGES.items():
            products = get_products_from_page(driver, url)
            write_to_csv(products, f"{product_type}.csv")


if __name__ == "__main__":
    get_all_products()
