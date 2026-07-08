import csv
from dataclasses import astuple, dataclass
from time import sleep
from urllib.parse import urljoin

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
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


FIELD_NAMES = [
    "title",
    "description",
    "price",
    "rating",
    "num_of_reviews",
]

PAGES = {
    "home": HOME_URL,
    "computers": urljoin(HOME_URL, "computers"),
    "laptops": urljoin(HOME_URL, "computers/laptops"),
    "tablets": urljoin(HOME_URL, "computers/tablets"),
    "phones": urljoin(HOME_URL, "phones"),
    "touch": urljoin(HOME_URL, "phones/touch"),
}


def clean_text(text: str) -> str:
    return " ".join(text.replace("\xa0", " ").split())


def click_more_until_all_products_loaded(driver: webdriver.Chrome) -> None:
    while True:
        buttons = driver.find_elements(
            By.CSS_SELECTOR,
            ".ecomerce-items-scroll-more",
        )

        if not buttons or not buttons[0].is_displayed():
            return

        driver.execute_script("arguments[0].click();", buttons[0])
        sleep(0.3)


def parse_product(product_card: WebElement) -> Product:
    title = product_card.find_element(By.CSS_SELECTOR, ".title")
    description = product_card.find_element(By.CSS_SELECTOR, ".description")
    price = product_card.find_element(By.CSS_SELECTOR, ".price")
    reviews = product_card.find_element(
        By.CSS_SELECTOR,
        "[itemprop='reviewCount']",
    )

    return Product(
        title=clean_text(title.get_attribute("title")),
        description=clean_text(description.text),
        price=float(clean_text(price.text).replace("$", "")),
        rating=len(
            product_card.find_elements(By.CSS_SELECTOR, ".ws-icon-star"),
        ),
        num_of_reviews=int(reviews.text),
    )


def get_products_from_page(
    driver: webdriver.Chrome,
    url: str,
) -> list[Product]:
    driver.get(url)

    WebDriverWait(driver, 10).until(
        lambda page: page.find_elements(By.CSS_SELECTOR, ".card.thumbnail")
        or page.find_elements(By.CSS_SELECTOR, ".ecomerce-items-scroll-more"),
    )
    click_more_until_all_products_loaded(driver)

    product_cards = driver.find_elements(By.CSS_SELECTOR, ".card.thumbnail")

    return [parse_product(product_card) for product_card in product_cards]


def write_products_to_csv(file_name: str, products: list[Product]) -> None:
    with open(file_name, "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(FIELD_NAMES)

        for product in products:
            writer.writerow(astuple(product))


def get_all_products() -> None:
    driver = webdriver.Chrome()

    try:
        for page_name, url in PAGES.items():
            products = get_products_from_page(driver, url)
            write_products_to_csv(f"{page_name}.csv", products)
    finally:
        driver.quit()


if __name__ == "__main__":
    get_all_products()
