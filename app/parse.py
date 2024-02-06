import csv
from dataclasses import dataclass, asdict, fields
from urllib.parse import urljoin

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from bs4 import BeautifulSoup

BASE_URL = "https://webscraper.io/"

PAGES = {
    "home": "test-sites/e-commerce/more/",
    "computers": "test-sites/e-commerce/more/computers",
    "phones": "test-sites/e-commerce/more/phones",
    "laptops": "test-sites/e-commerce/more/computers/laptops",
    "tablets": "test-sites/e-commerce/more/computers/tablets",
    "touch": "test-sites/e-commerce/more/phones/touch"
}


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


def initialize_driver() -> webdriver.Chrome:
    options = Options()
    options.add_argument("--headless")
    driver = webdriver.Chrome(options=options)
    return driver


def handle_cookies(driver: webdriver.Chrome) -> None:
    try:
        accept_cookies = WebDriverWait(driver, 5).until(
            ec.element_to_be_clickable((By.CLASS_NAME, "acceptCookies"))
        )
        accept_cookies.click()
    except Exception:
        pass


def handle_show_more(driver: webdriver.Chrome) -> None:
    while True:
        try:
            more_button = WebDriverWait(driver, 5).until(
                ec.element_to_be_clickable(
                    (By.CSS_SELECTOR, ".btn.ecomerce-items-scroll-more")
                )
            )
            more_button.click()
        except Exception:
            break


def parse_single_product(product_html: str) -> Product:
    soup = BeautifulSoup(product_html, "html.parser")
    rating = len(soup.select(".ws-icon"))
    return Product(
        title=soup.select_one(".title")["title"],
        description=soup.select_one(".description").get_text(strip=True),
        price=float(soup.select_one(".price").text.replace("$", "")),
        rating=rating,
        num_of_reviews=int(soup.select_one(".review-count").text.split(" ")[0])
    )


def write_product_to_csv(
        products: list[Product],
        filename: str
) -> None:
    with open(filename, "w", newline="") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[field.name for field in fields(Product)]
        )
        writer.writeheader()
        for product in products:
            writer.writerow(asdict(product))


def get_all_products() -> None:
    driver = initialize_driver()
    for name, link in PAGES.items():
        print(f"Processing {name} page...")
        driver.get(urljoin(BASE_URL, link))
        handle_show_more(driver)
        handle_cookies(driver)
        soup = BeautifulSoup(driver.page_source, "html.parser")
        products = [parse_single_product(
            str(product)
        ) for product in soup.select(".thumbnail")]
        write_product_to_csv(products, f"{name}.csv")
    driver.quit()


if __name__ == "__main__":
    get_all_products()
