import csv
import logging
import sys
from dataclasses import dataclass, astuple, fields
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common import TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions

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
    format="[%(levelname)8s] : %(message)s",
    handlers=[
        logging.FileHandler("parser.log"),
        logging.StreamHandler(sys.stdout),
    ],
)


def parse_single_product(product_soup: BeautifulSoup) -> Product:
    return Product(
        title=product_soup.select_one(".title")["title"],
        description=product_soup.select_one(".description").text.replace(
            "\xa0", " "
        ),
        price=float(product_soup.select_one(".price").text.replace("$", "")),
        rating=len(
            product_soup.find_all(
                "span", {"class": "glyphicon glyphicon-star"}
            )
        ),
        num_of_reviews=int(
            product_soup.select_one(".ratings > p.pull-right").text.split()[0]
        ),
    )


def get_product_from_page(page_source: str) -> list:
    page_soup = BeautifulSoup(page_source, "html.parser")
    products = page_soup.select(".thumbnail")
    return [parse_single_product(product) for product in products]


def get_all_products() -> None:
    options = Options()
    options.add_argument("--start-maximized")
    options.add_argument("--headless")
    driver = webdriver.Chrome(options=options)
    driver.get(HOME_URL)
    driver.find_element(By.CSS_SELECTOR, "#closeCookieBanner").click()
    number_of_main_links = len(
        driver.find_elements(By.XPATH, "//ul[@id='side-menu']/li/a")
    )
    for i in range(number_of_main_links):
        main_links = driver.find_elements(
            By.XPATH, "//ul[@id='side-menu']/li/a"
        )
        main_link = main_links[i]
        main_category_name = main_link.text
        logging.info(f"Start parsing page named {main_category_name}")
        main_link.click()
        main_category_products = get_product_from_page(driver.page_source)
        write_products_to_scv(main_category_products, main_category_name)
        wait = WebDriverWait(driver, 10)
        sub_links = driver.find_elements(
            By.CSS_SELECTOR, "#side-menu > li.active > ul > li > a"
        )
        for sub_i in range(len(sub_links)):
            sub_link = wait.until(
                expected_conditions.presence_of_all_elements_located(
                    (By.CSS_SELECTOR, "#side-menu > li.active > ul > li > a")
                )
            )[sub_i]
            sub_category_name = sub_link.text
            logging.info(f"Start parsing page named {sub_category_name}")
            sub_link.click()

            try_more_button = True
            while try_more_button:
                try:
                    wait = WebDriverWait(driver, 1)
                    button = wait.until(
                        expected_conditions.element_to_be_clickable(
                            (By.CSS_SELECTOR, "a.ecomerce-items-scroll-more")
                        )
                    )
                    driver.execute_script("arguments[0].click();", button)
                except TimeoutException:
                    try_more_button = False

            sub_category_products = get_product_from_page(driver.page_source)
            write_products_to_scv(sub_category_products, sub_category_name)

    driver.close()


def write_products_to_scv(products: [Product], product_page_name: str) -> None:
    product_csv_path = product_page_name.lower() + ".csv"
    with open(product_csv_path, "w") as file:
        writer = csv.writer(file, lineterminator="\n")
        writer.writerow(PRODUCT_FIELDS)
        writer.writerows([astuple(product) for product in products])


if __name__ == "__main__":
    get_all_products()
