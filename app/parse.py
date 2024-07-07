from dataclasses import dataclass
import time
import csv
from urllib.parse import urljoin

from selenium import webdriver
from selenium.common import TimeoutException, NoSuchElementException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.remote.webelement import WebElement
from tqdm import tqdm

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")
COMPUTERS_URL = HOME_URL + "computers/"
LAPTOPS_URL = COMPUTERS_URL + "laptops"
TABLETS_URL = COMPUTERS_URL + "tablets"
PHONES_URL = HOME_URL + "phones/"
TOUCH_URL = PHONES_URL + "touch"


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


def get_single_product(element: WebElement) -> Product:
    return Product(
        title=element.find_element(By.CLASS_NAME,
                                   "title").get_attribute("title"),
        description=element.find_element(By.CLASS_NAME, "description").text,
        price=float(
            element.find_element(By.CLASS_NAME, "price").text.replace("$", "")
        ),
        rating=len(element.find_elements(By.CLASS_NAME, "ws-icon-star")),
        num_of_reviews=int(
            element.find_element(By.CLASS_NAME, "ratings").text.split()[0]
        ),
    )


def setup_driver() -> webdriver.Chrome:
    options = Options()
    options.headless = True
    options.add_argument("--window-size=1920,1200")
    driver = webdriver.Chrome(options=options)
    return driver


def accept_cookies(driver: webdriver.Chrome) -> None:
    try:
        accept_cookies_button = WebDriverWait(driver, 2).until(
            EC.element_to_be_clickable((By.CLASS_NAME, "acceptCookies"))
        )
        accept_cookies_button.click()
        print("Cookies was accepted")
    except TimeoutException:
        print("No pop-up window accepting cookies")
    except NoSuchElementException:
        print("No item accepting cookies")


def parse_page(
    driver: webdriver.Chrome, url: str, with_pagination: bool = False
) -> [Product]:
    driver.get(url)
    accept_cookies(driver)
    products = []

    if with_pagination:
        while True:
            try:
                more_button = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable(
                        (By.CLASS_NAME, "btn.btn-primary.btn-lg.btn-block")
                    )
                )
                more_button.click()
                time.sleep(2)
            except TimeoutException:
                break
            except Exception as e:
                print("'Load More':", e)
                break

    time.sleep(3)
    product_elements = driver.find_elements(By.CLASS_NAME, "thumbnail")
    for elem in product_elements:
        product = get_single_product(elem)
        products.append(product)

    return products


def save_to_csv(filename: str, products: [Product]) -> None:
    with open(filename, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(
            ["title", "description", "price", "rating", "num_of_reviews"]
        )
        for product in products:
            writer.writerow(
                [
                    product.title,
                    product.description,
                    product.price,
                    product.rating,
                    product.num_of_reviews,
                ]
            )


def get_all_products() -> None:
    driver = setup_driver()

    pages_info = [
        ("home.csv", HOME_URL, False),
        ("computers.csv", COMPUTERS_URL, False),
        ("laptops.csv", LAPTOPS_URL, True),
        ("tablets.csv", TABLETS_URL, True),
        ("phones.csv", PHONES_URL, False),
        ("touch.csv", TOUCH_URL, True),
    ]

    for filename, url, with_pagination in tqdm(pages_info,
                                               desc="Scraping pages"):
        products = parse_page(driver, url, with_pagination)
        save_to_csv(filename, products)

    driver.quit()


if __name__ == "__main__":
    get_all_products()
