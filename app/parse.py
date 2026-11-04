import csv
from dataclasses import dataclass, fields, astuple

from bs4 import BeautifulSoup, Tag
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait
from tqdm import tqdm


BASE_URL = "https://webscraper.io/test-sites/e-commerce/more"

ACCEPT_COOKIES = "[data-tid='banner-accept']"
MORE_BUTTON = "a.ecomerce-items-scroll-more"
CARD = ".card-body"

PAGES = {
    "home": BASE_URL,
    "computers": f"{BASE_URL}/computers",
    "laptops": f"{BASE_URL}/computers/laptops",
    "tablets": f"{BASE_URL}/computers/tablets",
    "phones": f"{BASE_URL}/phones",
    "touch": f"{BASE_URL}/phones/touch",
}


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


PRODUCT_FIELDS = [field.name for field in fields(Product)]


def parse_single_product(product: Tag) -> Product:
    title = product.select_one(".title")["title"]
    description = product.select_one(".description").text.replace("\xa0", " ")
    price = float(product.select_one(".price").text.replace("$", ""))
    rating = len(product.select(".ratings .ws-icon-star"))
    num_of_reviews = int(product.select_one(".review-count span").text)

    return Product(
        title=title,
        price=price,
        description=description,
        rating=rating,
        num_of_reviews=num_of_reviews,
    )


def get_single_page_products(page_soup: BeautifulSoup) -> list[Product]:
    products = []
    cards = page_soup.select(CARD)
    for card in cards:
        products.append(parse_single_product(card))
    return products


def accept_cookies(driver: WebDriver) -> None:
    try:
        WebDriverWait(driver, 5).until(
            ec.element_to_be_clickable((By.CSS_SELECTOR, ACCEPT_COOKIES))
        ).click()
    except TimeoutException:
        pass


def load_all_products(driver: WebDriver) -> None:
    while True:
        buttons = driver.find_elements(By.CSS_SELECTOR, MORE_BUTTON)
        if not buttons or not buttons[0].is_displayed():
            break
        cards_count = len(driver.find_elements(By.CSS_SELECTOR, CARD))
        buttons[0].click()
        WebDriverWait(driver, 10).until(
            lambda d: len(d.find_elements(By.CSS_SELECTOR, CARD)) > cards_count
        )


def get_page_soup(driver: WebDriver, url: str) -> BeautifulSoup:
    driver.get(url)
    accept_cookies(driver)
    load_all_products(driver)
    html = driver.page_source
    soup = BeautifulSoup(html, "html.parser")
    return soup


def write_products_to_csv(products: list[Product], filename: str) -> None:
    with open(filename, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(PRODUCT_FIELDS)
        writer.writerows(astuple(product) for product in products)


def get_all_products() -> None:
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    driver = webdriver.Chrome(options=options)
    try:
        for name, url in tqdm(PAGES.items(), desc="Scraping pages"):
            file_name = f"{name}.csv"
            page_soup = get_page_soup(driver, url)
            single_page_products = get_single_page_products(page_soup)
            write_products_to_csv(single_page_products, file_name)
    finally:
        driver.quit()


if __name__ == "__main__":
    get_all_products()
