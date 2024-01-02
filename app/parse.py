import csv
from selenium.webdriver.support import expected_conditions as EC
from dataclasses import dataclass, fields, astuple
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.wait import WebDriverWait

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")
PHONES_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/phones")
COMPUTERS_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/computers")
TOUCH_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/phones/touch")
TABLETS_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/computers/tablets")
LAPTOPS_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/computers/laptops")


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


PRODUCT_FIELDS = [field.name for field in fields(Product)]

_driver: WebDriver | None = None


def get_driver() -> WebDriver:
    return _driver


def set_driver(new_driver: WebDriver) -> None:
    global _driver
    _driver = new_driver


def parse_single_product(product_soup: BeautifulSoup) -> Product:
    return Product(
        title=product_soup.select_one(".title")["title"],
        description=product_soup.select_one("p[class*=description]").text,
        price=float(product_soup.select_one("h4[class*=price]").text.replace("$", "")),
        rating=len(product_soup.select(".ws-icon-star")),
        num_of_reviews=int(product_soup.select_one("p[class*=review-count]").text.split()[0]),
    )


def accept_cookies(driver: WebDriver):
    try:
        accept_cookies_button = driver.find_element(By.CLASS_NAME, "acceptContainer")
        accept_cookies_button.click()
    except NoSuchElementException:
        pass


def get_products_from_page(url: str) -> [Product]:
    driver = get_driver()
    driver.get(url)
    accept_cookies(driver)

    try:
        while True:
            more_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CLASS_NAME, "ecomerce-items-scroll-more"))
            )
            if not more_button.is_displayed():
                break
            more_button.click()
            WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.CLASS_NAME, "thumbnail")))

    except NoSuchElementException:
        pass
    except TimeoutException:
        pass

    page = driver.page_source
    soup = BeautifulSoup(page, "html.parser")
    products = soup.select(".thumbnail")
    return [parse_single_product(product_soup) for product_soup in products]


def write_products_to_csv(products: [Product], csv_patch: str) -> None:
    with open(csv_patch, "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(PRODUCT_FIELDS)
        writer.writerows([astuple(product) for product in products])


def get_all_products() -> None:
    with webdriver.Chrome() as new_driver:
        set_driver(new_driver)
        home_products = get_products_from_page(HOME_URL)
        write_products_to_csv(home_products, "home.csv")
        phone_products = get_products_from_page(PHONES_URL)
        write_products_to_csv(phone_products, "phones.csv")
        computer_products = get_products_from_page(COMPUTERS_URL)
        write_products_to_csv(computer_products, "computers.csv")
        touch_products = get_products_from_page(TOUCH_URL)
        write_products_to_csv(touch_products, "touch.csv")
        tablets_products = get_products_from_page(TABLETS_URL)
        write_products_to_csv(tablets_products, "tablets.csv")
        laptop_products = get_products_from_page(LAPTOPS_URL)
        write_products_to_csv(laptop_products, "laptops.csv")


if __name__ == "__main__":
    get_all_products()
