import csv
import logging
import sys
import time
from dataclasses import dataclass, astuple, fields
from typing import List
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common import TimeoutException, ElementClickInterceptedException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait
from tqdm import tqdm


BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")

logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)8s]: %(message)s",
    handlers=[
        logging.FileHandler("parser.log"),
        logging.StreamHandler(sys.stdout),
    ]
)


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


PRODUCT_FIELDS = [field.name for field in fields(Product)]


def check_cookies(driver: WebDriver) -> None:
    try:
        button = WebDriverWait(driver, 5).until(
            expected_conditions.element_to_be_clickable(
                (By.CLASS_NAME, "acceptCookies")
            )
        )
        button.click()
    except TimeoutException:
        logging.info("Cookie acceptance button not found or not clickable.")


def get_all_urls(driver: WebDriver, url: str) -> List[str]:
    logging.info("Link collection begins.")

    driver.get(url)
    check_cookies(driver)

    category_links = driver.find_elements(
        By.CSS_SELECTOR,
        "a[class*='category-link']"
    )
    category_full_links = [
        urljoin(url, link.get_attribute("href"))
        for link in category_links
    ]

    subcategory_full_links = []

    for link in category_full_links:
        driver.get(link)
        subcategory_links = driver.find_elements(
            By.CSS_SELECTOR,
            "a[class*='subcategory-link']"
        )
        sub_links = [
            urljoin(url, link.get_attribute("href"))
            for link in subcategory_links
        ]
        subcategory_full_links.extend(sub_links)
        driver.implicitly_wait(2)

    all_links = [url] + category_full_links + subcategory_full_links

    logging.info(f"All links collected. Number of links {len(all_links)}.")

    return all_links


def get_single_product(product: BeautifulSoup) -> Product:
    title = product.select_one(".title")["title"]
    description = product.select_one(".description").text.replace("\xa0", " ")
    price = float(product.select_one(".price").text.replace("$", ""))
    rating = len(product.select("span.ws-icon.ws-icon-star"))
    num_of_reviews = int(product.select_one(".review-count").text.split()[0])

    return Product(
        title=title,
        description=description,
        price=price,
        rating=rating,
        num_of_reviews=num_of_reviews
    )


def get_single_page(page_soup: BeautifulSoup) -> List[Product]:
    products = page_soup.select(".product-wrapper")

    return [get_single_product(product) for product in products]


def get_all_page_products(driver: WebDriver, url: str) -> List[Product]:
    driver.get(url)

    while True:
        try:
            more_button = WebDriverWait(driver, 1).until(
                expected_conditions.element_to_be_clickable(
                    (By.CLASS_NAME, "ecomerce-items-scroll-more")
                )
            )

            driver.execute_script(
                "arguments[0].scrollIntoView(true);",
                more_button
            )

            more_button.click()
            time.sleep(1)
        except TimeoutException:
            logging.error("The waiting time was exceeded.")
            break
        except ElementClickInterceptedException as e:
            logging.error(f"More button not found: {e}")
            break

    logging.info("Start parsing page.")

    soup = BeautifulSoup(driver.page_source, "html.parser")
    products = get_single_page(soup)

    logging.info(f"Products collected: {len(products)}.")
    logging.info("Stop parsing page.")

    return products


def write_to_csv(products: List[Product], url: str) -> None:
    logging.info("Start writing to file.")

    name = f"{url.rstrip("/").rsplit("/", 1)[-1]}.csv"

    if name == "more.csv":
        name = "home.csv"

    with open(name, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(PRODUCT_FIELDS)
        writer.writerows([astuple(product) for product in products])

    logging.info("End of writing to file.")


def get_all_products() -> None:
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")

    with webdriver.Chrome(options=chrome_options) as driver:
        urls = get_all_urls(driver, HOME_URL)

        for url in tqdm(urls):
            products = get_all_page_products(driver, url)

            write_to_csv(products, url)


if __name__ == "__main__":
    get_all_products()
