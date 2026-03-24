import csv
import logging
import random
import sys
import time
from dataclasses import dataclass, fields, astuple
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup, Tag
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from tqdm import tqdm


ROOT_URL = "https://webscraper.io"
BASE_URL = "https://webscraper.io/test-sites/e-commerce/more/"
HOME_URL = f'{BASE_URL}'
COMPUTERS_URL = f'{BASE_URL}computers/'
LAPTOPS_URL = f'{BASE_URL}computers/laptops'
TABLETS_URL = f'{BASE_URL}computers/tablets'
PHONES_URL = f'{BASE_URL}phones'
TOUCH_URL = f'{BASE_URL}phones/touch'


def get_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    return webdriver.Chrome(options=options)


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


PRODUCT_FIELDS = [field.name for field in fields(Product)]


logging.basicConfig(
    level=logging.DEBUG,
    format="[%(levelname)8s]: %(message)s",
    handlers=[
        logging.FileHandler("parser.log"),
        logging.StreamHandler(sys.stdout),
    ]
)


def click_accept_button(product_soup: Tag, driver) -> None:
    relative_url = product_soup.select_one(".title")["href"]
    product_url = urljoin(ROOT_URL, relative_url)
    driver.get(product_url)
    try:
        wait = WebDriverWait(driver, 5)
        cookie_button = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "acceptCookies")))
        cookie_button.click()
        time.sleep(0.5)
        print("Cookies accepted")
    except TimeoutException:
        print("There is no Cookie banner")
    except Exception as e:
        print(f"Error excepting cookies {e}")
    # swatches = driver.find_element(By.CLASS_NAME, "swatches")
    # buttons = swatches.find_elements(By.TAG_NAME, "button")
    # prices_dict = {}
    # for button in buttons:
    #     if not button.get_property("disabled"):
    #         button.click()
    #         prices_dict[button.get_property("value")] = float(
    #             driver.find_element(By.CLASS_NAME, "price").text.replace("$", "")
    #         )
    # all_prices = list(prices_dict.values())
    # if not all_prices:
    #     base_price = float(product_soup.select_one(".price").text.replace("$", ""))
    #     all_prices = [base_price]
    # return all_prices


def parse_single_product(product_soup: Tag) -> Product:
    title_el = product_soup.select_one(".title")
    description_el = product_soup.select_one(".description")
    price_el = product_soup.select_one(".price")
    stars = product_soup.select(".ws-icon-star")
    print(f'printing rating{stars}')
    num_of_reviews_el = product_soup.select_one(".review-count")
    return Product(
        title=title_el["title"] if title_el else "No title",
        description=description_el.get_text(strip=True) if description_el else "No description",
        price=float(price_el.get_text(strip=True).replace("$", "")) if price_el else 0.00,
        rating=len(stars) if stars else 0,
        num_of_reviews=int(num_of_reviews_el.text.split()[0]) if num_of_reviews_el else 0,
    )


def write_products_to_csv(products: [Product], file_name: str):
    with open(file_name, "w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(PRODUCT_FIELDS)
        writer.writerows(astuple(product) for product in products)
    print(f"-------Save {len(products)} in {file_name}-------")


def scrape_page(url: str, file_name: str, limit: int = None, has_pagination: bool = False):
    driver = get_driver()
    driver.get(url)
    try:
        wait = WebDriverWait(driver, 5)
        cookie_button = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "acceptCookies")))
        cookie_button.click()
        time.sleep(0.5)
        print("Cookies accepted")
    except TimeoutException:
        print("There is no Cookie banner")

    if has_pagination:
        while True:
            try:
                more_button = driver.find_element(By.CSS_SELECTOR, ".ecomerce-items-scroll-more")
                if not more_button.is_displayed():
                    break
                driver.execute_script("arguments[0].click();", more_button)
                time.sleep(1)
            except NoSuchElementException:
                break
        time.sleep(2)
    soup = BeautifulSoup(driver.page_source, "html.parser")
    all_cards = soup.select(".thumbnail")

    print(f"Found {len(all_cards)} on the page")

    if limit and len(all_cards) > limit:
        selected_cards = random.sample(all_cards, k=limit)
    else:
        selected_cards = all_cards
    products = [parse_single_product(card) for card in selected_cards]
    write_products_to_csv(products, file_name)
    driver.quit()


def get_all_products() -> None:
    scrape_page(HOME_URL, "home.csv", limit=3)
    scrape_page(COMPUTERS_URL, "computers.csv", limit=3)
    scrape_page(LAPTOPS_URL, "laptops.csv", has_pagination=True)
    scrape_page(TABLETS_URL, "tablets.csv", has_pagination=True)
    scrape_page(PHONES_URL, "phones.csv", limit=3)
    scrape_page(TOUCH_URL, "touch.csv", has_pagination=True)


if __name__ == "__main__":
    get_all_products()
