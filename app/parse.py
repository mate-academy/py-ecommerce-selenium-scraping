import csv
import logging
from dataclasses import dataclass, astuple, fields
from urllib.parse import urljoin

from selenium import webdriver
from selenium.common import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.webdriver import WebDriver
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions
from bs4 import BeautifulSoup, Tag
from tqdm import tqdm

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")

logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)8s]: %(message)s",
    handlers=[
        logging.FileHandler("parser.log"),
    ],
)


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


QUOTE_FIELDS = [field.name for field in fields(Product)]


def set_driver() -> WebDriver:
    options = Options()
    options.add_argument("-headless")
    options.set_preference(name="permissions.default.image", value=2)
    driver = webdriver.Firefox(options=options)

    return driver


def accept_cookies(driver: WebDriver) -> None:
    try:
        cookies_btn = WebDriverWait(driver, 1).until(
            expected_conditions.presence_of_element_located(
                (By.CLASS_NAME, "acceptCookies")
            )
        )
        cookies_btn.click()
        logging.info("Accepted 'Cookie'")
    except TimeoutException:
        logging.info("Button 'Cookie' not found")


def get_page_source(url_to_parse: str, driver: WebDriver) -> str:
    url = urljoin(HOME_URL, url_to_parse)
    logging.info(f"Start parsing page {url}")
    driver.get(url)
    accept_cookies(driver)
    wait = WebDriverWait(driver, timeout=1)

    try:
        more_btn = wait.until(
            expected_conditions.presence_of_element_located(
                (By.CLASS_NAME, "ecomerce-items-scroll-more")
            )
        )

        while wait.until(lambda d: more_btn.is_displayed()):
            logging.info(f"Clicking 'More' button on {url}")
            more_btn.click()
    except TimeoutException:
        logging.info(f"Button 'More' not found on {url}")

    return driver.page_source


def parse_singe_quote(product_soup: Tag) -> Product:
    return Product(
        title=product_soup.select_one(".title")["title"],
        description=product_soup.select_one(".description").text.replace(
            "\xa0", " "
        ),
        price=float(product_soup.select_one(".price").text.replace("$", "")),
        rating=len(product_soup.select(".ws-icon-star")),
        num_of_reviews=int(
            product_soup.select_one("p.pull-right").text.split()[0]
        ),
    )


def get_single_page_products(page_source: str) -> [Product]:
    soup = BeautifulSoup(markup=page_source, features="html.parser")
    products = soup.select(".thumbnail")

    return [
        parse_singe_quote(product_soup=product_soup)
        for product_soup in products
    ]


def write_products_to_csv(products: [Product], path: str) -> None:
    with open(path, "w") as file:
        writer = csv.writer(file)
        writer.writerow(QUOTE_FIELDS)
        writer.writerows(astuple(product) for product in products)


def get_all_products() -> None:
    urls_to_parse = {
        "home": "",
        "computers": "computers",
        "laptops": "computers/laptops",
        "tablets": "computers/tablets",
        "phones": "phones",
        "touch": "phones/touch",
    }
    driver = set_driver()

    for filename, url_to_parse in tqdm(urls_to_parse.items()):
        page_source = get_page_source(driver=driver, url_to_parse=url_to_parse)
        products = get_single_page_products(page_source)
        path = filename + ".csv"
        write_products_to_csv(products=products, path=path)

    driver.close()


if __name__ == "__main__":
    get_all_products()
