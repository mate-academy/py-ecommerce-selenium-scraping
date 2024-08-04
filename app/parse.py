import csv
import time
from dataclasses import dataclass, fields
from multiprocessing import Pool
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import (
    ElementNotInteractableException,
    NoSuchElementException
)
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from tqdm import tqdm


BASE_URL = "https://webscraper.io/"

PRODUCT_URLS = {
    "home": urljoin(BASE_URL, "test-sites/e-commerce/more"),
    "computers": urljoin(
        BASE_URL,
        "test-sites/e-commerce/more/computers"
    ),
    "laptops": urljoin(
        BASE_URL,
        "test-sites/e-commerce/more/computers/laptops"
    ),
    "tablets": urljoin(
        BASE_URL,
        "test-sites/e-commerce/more/computers/tablets"
    ),
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


QUOTE_FIELDS = [field.name for field in fields(Product)]


def accept_cookie(driver: webdriver.Chrome) -> None:
    button_accept_cookie = driver.find_element(
        By.CSS_SELECTOR,
        ".acceptCookies"
    )
    if button_accept_cookie:
        time.sleep(0.1)
        button_accept_cookie.click()


def driver_check_click_more_button(driver: webdriver.Chrome, url: str) -> str:
    time.sleep(0.1)
    clicks = 0
    while True:
        try:
            button_more = driver.find_element(
                By.CSS_SELECTOR,
                ".btn.btn-lg.btn-block.btn-primary.ecomerce-items-scroll-more",
            )
            time.sleep(0.1)
            button_more.click()
            clicks += 1
            time.sleep(0.1)
        except NoSuchElementException:
            print(
                f"\033[93mThe 'More' button not found or has expired. "
                f"URL: {url}\033[0m"
            )
            break
        except ElementNotInteractableException:
            print(
                f"\033[93mThe 'More' button not found or has expired. "
                f"URL: {url}\033[0m"
            )
            break
    print(f"\033[93m{clicks} clicks on 'More' button for url {url}\033[0m")


def parse_single_product(product_soup: BeautifulSoup) -> Product:
    return Product(
        title=product_soup.select_one(".title")["title"],
        description=(product_soup.select_one(".description").text)
        .replace("\xa0", " ")
        .strip(),
        price=float((product_soup.select_one(".price").text).replace("$", "")),
        rating=len(product_soup.find_all(class_="ws-icon ws-icon-star")),
        num_of_reviews=int(
            (product_soup.select_one(".review-count").text).rstrip(" reviews")
        ),
    )


def parse_products(url: str) -> list:
    chrome_options = Options()
    chrome_options.add_argument("--headless")

    service = ChromeService()
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.get(url)
    time.sleep(1)
    accept_cookie(driver=driver)
    driver_check_click_more_button(driver=driver, url=url)

    product_cards = driver.find_elements(
        By.CSS_SELECTOR,
        ".product-wrapper.card-body"
    )
    products = []

    for card in product_cards:
        card_html = card.get_attribute("outerHTML")
        card_soup = BeautifulSoup(card_html, "html.parser")
        products.append(parse_single_product(card_soup))

    print(f"\033[92mFind: {len(products)} products in {url}\033[0m")
    driver.close()

    return products


def save_to_csv(products: list, filename: str) -> None:
    with open(filename, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=QUOTE_FIELDS)
        writer.writeheader()
        for product in products:
            writer.writerow(
                {
                    "title": product.title,
                    "description": product.description,
                    "price": product.price,
                    "rating": product.rating,
                    "num_of_reviews": product.num_of_reviews,
                }
            )


def parse_url(key_url: tuple) -> tuple:
    key, url = key_url
    products = parse_products(url)
    return (key, products)


def get_all_products() -> None:
    with Pool(processes=6) as pool:
        results = list(
            tqdm(
                pool.imap(parse_url, PRODUCT_URLS.items()),
                total=len(PRODUCT_URLS),
                desc="Parsing products",
            )
        )

    for key, products in results:
        filename = f"{key}.csv"
        save_to_csv(products, filename)
        print(f"Saved {len(products)} products to {filename}")


if __name__ == "__main__":
    get_all_products()
