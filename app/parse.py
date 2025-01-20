import csv
import time
from dataclasses import dataclass, fields
from urllib.parse import urljoin

from selenium import webdriver
from selenium.common import TimeoutException, NoSuchElementException
from selenium.webdriver import ActionChains
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from tqdm import tqdm


BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")
COMPUTERS = urljoin(HOME_URL, "computers/")
LAPTOPS = urljoin(HOME_URL, "computers/laptops/")
TABLETS = urljoin(HOME_URL, "computers/tablets/")
PHONES = urljoin(HOME_URL, "phones/")
TOUCH = urljoin(HOME_URL, "phones/touch/")

CSV_FILES = {
    "home": "home.csv",
    "computers": "computers.csv",
    "laptops": "laptops.csv",
    "tablets": "tablets.csv",
    "phones": "phones.csv",
    "touch": "touch.csv",
}

PAGES = {
    "home": HOME_URL,
    "computers": COMPUTERS,
    "laptops": LAPTOPS,
    "tablets": TABLETS,
    "phones": PHONES,
    "touch": TOUCH,
}


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


PRODUCT_FIELDS = [field.name for field in fields(Product)]


def setup_driver(headless: bool = True) -> webdriver.Chrome:
    chrome_options = Options()
    if headless:
        chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(options=chrome_options)
    return driver


def accept_cookies(driver: webdriver) -> None:
    try:
        WebDriverWait(driver, 10).until(
            ec.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler"))
        ).click()
    except TimeoutException:
        print("No cookie banner found.")
    except NoSuchElementException:
        print("Cookie banner element not found.")


def scroll_page(driver: webdriver, max_scroll_attempts: int = 10) -> None:
    scroll_attempts = 0
    while scroll_attempts < max_scroll_attempts:
        try:
            button = WebDriverWait(driver, 10).until(
                ec.presence_of_element_located(
                    (By.CLASS_NAME, "ecomerce-items-scroll-more")
                )
            )
            ActionChains(driver).move_to_element(button).perform()
            button.click()
            time.sleep(2)
            scroll_attempts += 1
        except (NoSuchElementException, TimeoutException):
            print("Button 'More' not found or not clickable. Scroll ended.")
            break
        except Exception as e:
            print(f"Unexpected error during scrolling: {e}")
            break
    else:
        print("Limit of scroll attempts reached.")


def parse_single_product(product: WebElement) -> Product:
    title = product.find_element(By.CLASS_NAME, "title").get_property("title")
    description = product.find_element(By.CLASS_NAME, "description").text
    price = float(product.find_element(By.CLASS_NAME, "price")
                  .text.replace("$", ""))
    rating_elements = product.find_elements(By.CLASS_NAME, "ws-icon-star")
    rating = len(rating_elements) if rating_elements else 0
    num_of_reviews = int(product.find_element(By.CLASS_NAME, "review-count")
                         .text.strip().split()[0])
    return Product(title=title,
                   description=description,
                   price=price,
                   rating=rating,
                   num_of_reviews=num_of_reviews)


def parse_product_on_page(driver: webdriver, url: str) -> list[Product]:
    driver.get(url)
    accept_cookies(driver)
    scroll_page(driver)

    products_elements = driver.find_elements(By.CLASS_NAME, "thumbnail")
    products = [parse_single_product(product) for product in products_elements]
    return products


def save_products_to_csv(products: list[Product], file_path: str) -> None:
    with open(file_path, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=PRODUCT_FIELDS)
        writer.writeheader()
        for product in products:
            writer.writerow(product.__dict__)


def get_all_products() -> None:
    driver = setup_driver()

    try:
        for page_name, page_url in tqdm(PAGES.items(), desc="Parsing pages"):
            print(f"Parsing page {page_name}...")
            products = parse_product_on_page(driver, page_url)
            csv_file = CSV_FILES[page_name]
            save_products_to_csv(products, csv_file)
            print(f"Saved {len(products)} products to {csv_file}.")
    finally:
        driver.quit()


if __name__ == "__main__":
    get_all_products()
