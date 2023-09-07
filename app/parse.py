import csv
import logging
import os
import sys
from dataclasses import dataclass, fields, astuple
from urllib.parse import urljoin
from tqdm import tqdm
from selenium.common import TimeoutException
from selenium.webdriver import ChromeOptions, Chrome
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as ec
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


PRODUCT_FIELDS = [field.name for field in fields(Product)]


logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)8s]: %(message)s",
    handlers=[
        logging.FileHandler(os.path.join("parser.log")),
        logging.StreamHandler(sys.stdout),
    ],
)


def get_driver() -> Chrome:
    options = ChromeOptions()
    options.add_argument("--headless")
    driver = Chrome(options=options)
    return driver


def get_sub_links(link: str, driver: Chrome) -> list[str]:
    driver.get(link)
    sub_links = driver.find_elements(
        By.CSS_SELECTOR, "ul.nav-second-level > li > a"
    )
    return [sub_link.get_attribute("href") for sub_link in sub_links]


def get_all_links(driver: WebDriver) -> list[str]:
    links = []
    sub_links = []
    driver.get(HOME_URL)
    sidebar = driver.find_elements(
        By.CSS_SELECTOR, ".sidebar-nav > ul > li > a"
    )

    logging.info("Getting base links")

    for link in tqdm(sidebar):
        links.append(link.get_attribute("href"))

    logging.info("Getting sub links")

    for link in tqdm(links):
        sub_links.extend(get_sub_links(link, driver))
    links.extend(sub_links)

    return links


def write_to_file(filename: str, list_of_products: list[Product]) -> None:
    with open(filename, "w", encoding="utf-8", newline="") as products_file:
        writer = csv.writer(products_file)
        writer.writerow(PRODUCT_FIELDS)
        writer.writerows([astuple(product) for product in list_of_products])


def get_page_and_file_name(link: str) -> tuple[str, str]:
    page_name = link.split("/")[-1]
    if page_name == "more":
        page_name = "home"
    return page_name, page_name + ".csv"


def accept_cookies(driver: WebDriver) -> None:
    cookies = driver.find_elements(By.CLASS_NAME, "acceptCookies")
    if cookies:
        try:
            WebDriverWait(driver, 10).until(
                ec.element_to_be_clickable((By.CLASS_NAME, "acceptCookies"))
            ).click()
        except Exception as e:
            print("Error while accepting cookies:", e)


def get_full_page(driver: WebDriver) -> None:
    accept_cookies(driver)
    more = driver.find_elements(
        By.CLASS_NAME,
        "ecomerce-items-scroll-more"
    )
    if not more:
        return
    more_button = more[0]
    logging.info("Getting full page")
    while more_button.is_displayed():
        try:
            more_button = WebDriverWait(driver, 10).until(
                ec.presence_of_element_located(
                    (By.CLASS_NAME, "ecomerce-items-scroll-more"))
            )
            more_button.click()
        except ElementNotInteractableException:
            continue
        except TimeoutException:
            break


def get_page_products(driver: WebDriver, link: str) -> list:
    driver.get(link)
    get_full_page(driver)
    products_elements = driver.find_elements(By.CLASS_NAME, "thumbnail")
    return [products_element for products_element in tqdm(products_elements)]


def parse_product(product_element: WebElement) -> Product:
    product = Product(
        title=product_element.find_element(
            By.CLASS_NAME,
            "title"
        ).get_attribute("title"),
        description=product_element.find_element(
            By.CLASS_NAME,
            "description"
        ).text,
        price=float(
            product_element.find_element(
                By.CLASS_NAME,
                "price"
            ).text.replace("$", "")),
        rating=len(
            product_element.find_elements(
                By.CLASS_NAME,
                "ws-icon-star"
            )
        ),
        num_of_reviews=int(
            product_element.find_element(
                By.CSS_SELECTOR,
                "div.ratings > p.pull-right"
            ).text.split()[0]
        )
    )
    return product


def get_all_products() -> None:

    driver = get_driver()
    links = get_all_links(driver)
    for link in links:
        page_name, file_name = get_page_and_file_name(link)

        logging.info(f"Getting products from page {page_name}")
        products_elements = get_page_products(driver=driver, link=link)

        logging.info("Parsing products")

        products = [
            parse_product(
                product_element
            ) for
            product_element in tqdm(
                products_elements
            )
        ]

        logging.info(f"Writing products to {file_name}")
        write_to_file(file_name, products)
    driver.close()


if __name__ == "__main__":
    get_all_products()
