import csv

from dataclasses import dataclass, fields, astuple
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec

chrome_options = Options()
chrome_options.add_argument("--headless")
driver = webdriver.Chrome(options=chrome_options)

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")
COMPUTERS_URL = urljoin(HOME_URL, "computers/")
LAPTOPS_URL = urljoin(COMPUTERS_URL, "laptops")
TABLETS_URL = urljoin(COMPUTERS_URL, "tablets")
PHONES_URL = urljoin(HOME_URL, "phones/")
TOUCH_URL = urljoin(PHONES_URL, "touch")


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


PRODUCT_FIELDS = [field.name for field in fields(Product)]


def get_single_product(product: BeautifulSoup) -> Product:
    return Product(
        title=product.select_one("a.title").get("title"),
        description=product.select_one(".description")
        .text.strip()
        .replace("\xa0", " "),
        rating=len(
            product.select_one(".ratings p:not(.review-count)").select("span")
        ),
        price=float(product.select_one(".price").text.replace("$", "")),
        num_of_reviews=int(
            product.select_one(".review-count").text.split()[0]
        ),
    )


def get_list_products(url: str) -> list[Product]:
    driver.get(url)
    products_list = []
    driver.get(url)
    try:
        WebDriverWait(driver, 1).until(
            ec.presence_of_element_located(
                (By.CSS_SELECTOR, ".product-wrapper")
            )
        )
        accept_button = WebDriverWait(driver, 1).until(
            ec.element_to_be_clickable(
                (By.CSS_SELECTOR, "button[data-tid='banner-accept']")
            )
        )
        accept_button.click()
    except Exception:
        pass
    while True:
        try:
            more = driver.find_element(
                By.CSS_SELECTOR, ".ecomerce-items-scroll-more"
            )
        except Exception:
            break
        else:
            try:
                more.click()
            except Exception:
                break
    soup = BeautifulSoup(driver.page_source, "html.parser")
    products = soup.select(".product-wrapper")

    products_list.extend([get_single_product(product) for product in products])
    return products_list


def write_csv(url: str, filename: str) -> None:
    with open(filename, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(PRODUCT_FIELDS)
        writer.writerows([astuple(quote) for quote in get_list_products(url)])


def get_all_products() -> None:
    products = {
        HOME_URL: "home.csv",
        COMPUTERS_URL: "computers.csv",
        TOUCH_URL: "touch.csv",
        TABLETS_URL: "tablets.csv",
        LAPTOPS_URL: "laptops.csv",
        PHONES_URL: "phones.csv",
    }
    for url, filename in products.items():
        write_csv(url, filename)
    driver.close()
