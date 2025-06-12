import csv
from dataclasses import dataclass, fields, astuple
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup, Tag
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")
COMPUTER_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/computers")
PHONES_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/phones")
TOUCH_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/phones/touch")
TABLETS_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/computers/tablets")
LAPTOP_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/computers/laptops")

driver: WebDriver | None = None

def initialize_driver() -> None:
    global driver
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    service = Service()
    globals()['driver'] = webdriver.Chrome(service=service, options=chrome_options)

@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Product):
            return False
        return (
            self.title == other.title
            and self.description == other.description
            and self.price == other.price
            and self.rating == other.rating
            and self.num_of_reviews == other.num_of_reviews
        )

PRODUCT_FIELDS = [field.name for field in fields(Product)]

def parse_single_product(product: Tag) -> Product:
    rating = len(product.select("p span.ws-icon.ws-icon-star"))
    description = product.select_one(".description.card-text").text.replace("\xa0", " ").strip()
    return Product(
        title=product.select_one(".title")["title"],
        description=description,
        price=float(product.select_one(".price").text.replace("$", "")),
        rating=rating,
        num_of_reviews=int(product.select_one(".review-count").text.split()[0]),
    )

def get_products(url: str) -> list[Product]:
    text = requests.get(url).content
    soup = BeautifulSoup(text, "html.parser")
    products = soup.select(".product-wrapper.card-body")
    return [parse_single_product(product) for product in products]

def get_products_multi_page(url: str) -> list[Product]:
    global driver
    driver.get(url)
    while True:
        try:
            wait = WebDriverWait(driver, 1)
            more_button = wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, ".btn.btn-lg.btn-block.btn-primary.ecomerce-items-scroll-more"))
            )
            ActionChains(driver).move_to_element(more_button).click().perform()
        except Exception:
            break
    page_source = driver.page_source
    soup = BeautifulSoup(page_source, "html.parser")
    products = soup.select(".product-wrapper.card-body")
    return [parse_single_product(product) for product in products]

def write_products_to_csv(name: str, products: list[Product]) -> None:
    with open(name, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(PRODUCT_FIELDS)
        writer.writerows([astuple(product) for product in products])

def get_all_products() -> None:
    initialize_driver()
    write_products_to_csv("home.csv", get_products(HOME_URL))
    write_products_to_csv("computers.csv", get_products(COMPUTER_URL))
    write_products_to_csv("phones.csv", get_products(PHONES_URL))
    write_products_to_csv("touch.csv", get_products_multi_page(TOUCH_URL))
    write_products_to_csv("tablets.csv", get_products_multi_page(TABLETS_URL))
    write_products_to_csv("laptops.csv", get_products_multi_page(LAPTOP_URL))
    if driver:
        driver.quit()

if __name__ == "__main__":
    get_all_products()
