import csv

from dataclasses import dataclass, fields, astuple
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common import NoSuchElementException, TimeoutException
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait
from tqdm import tqdm


BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")


URLS = {
    "home.csv": HOME_URL,
    "computers.csv": urljoin(HOME_URL, "computers"),
    "laptops.csv": urljoin(HOME_URL, "computers/laptops"),
    "tablets.csv": urljoin(HOME_URL, "computers/tablets"),
    "phones.csv": urljoin(HOME_URL, "phones"),
    "touch.csv": urljoin(HOME_URL, "phones/touch"),
}


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


PRODUCT_FIELDS = [field.name for field in fields(Product)]


def parse_single_product(product_soup: BeautifulSoup) -> Product:
    return Product(
        title=product_soup.select_one(".title")["title"],
        description=product_soup.select_one(".description").text.replace(
            " ", " "
        ),
        price=float(product_soup.select_one(".price").text.replace("$", "")),
        rating=len(
            product_soup.select("div.ratings > p > span.ws-icon.ws-icon-star")
        ),
        num_of_reviews=int(
            product_soup.select_one(".ratings > p.pull-right").text.split()[0]
        ),
    )


def accept_cookie(driver: WebDriver) -> None:
    try:
        cookie_button = WebDriverWait(driver, 1).until(
            expected_conditions.presence_of_element_located(
                (By.CLASS_NAME, "acceptCookies")
            )
        )
        cookie_button.click()
    except (NoSuchElementException, TimeoutException):
        pass


def more_button(driver: WebDriver, url: str) -> BeautifulSoup:

    driver.get(url)

    try:
        more_but = driver.find_element(
            By.CLASS_NAME, "ecomerce-items-scroll-more"
        )
    except NoSuchElementException:
        more_but = None

    while more_but:
        if not more_but.is_displayed():
            break
        driver.execute_script("arguments[0].click();", more_but)

    return BeautifulSoup(driver.page_source, "html.parser")


def get_single_page_products(driver: WebDriver, url: str) -> [Product]:
    soup = more_button(driver, url)
    products = soup.select(".thumbnail")

    products_list = []
    for product_soup in tqdm(products, desc=f"Scraping Products on {url}"):
        product = parse_single_product(product_soup)
        products_list.append(product)

    return products_list


def write_products_to_csv(csv_output_path: str, products: [Product]) -> None:
    with open(csv_output_path, "w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(PRODUCT_FIELDS)
        writer.writerows([astuple(product) for product in products])


def get_all_products() -> None:
    options = Options()
    options.add_argument("--headless")
    driver = webdriver.Edge(options=options)
    with driver as new_driver:
        for category, url in URLS.items():
            accept_cookie(new_driver)
            products = get_single_page_products(driver, url)
            write_products_to_csv(category, products)


if __name__ == "__main__":
    get_all_products()
