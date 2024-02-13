import csv
import logging
import sys
from dataclasses import dataclass, fields, astuple
from time import sleep
from urllib.parse import urljoin

from selenium import webdriver
from selenium.common import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement

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

_driver: WebDriver | None = None


def get_driver() -> WebDriver:
    return _driver


def set_driver(new_driver: WebDriver) -> None:
    global _driver
    _driver = new_driver


logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)8s]:  %(message)s)",
    handlers=[
        logging.FileHandler("parser.log"),
        logging.StreamHandler(
            sys.stdout,
        ),
    ],
)


def write_csv(path: str, items: list, column_headings: list) -> None:
    logging.info(f"Start writing to {path}")
    with open(path, "w", newline="", encoding="utf-8") as file:
        quote_writer = csv.writer(file)
        quote_writer.writerow(column_headings)
        quote_writer.writerows([astuple(quote) for quote in items])


def start_accept_cookies_get_list_main_url(url: str) -> list[str]:
    driver = get_driver()

    driver.get(url)
    driver.find_element(By.CLASS_NAME, "acceptCookies").click()
    side_menu = driver.find_element(By.ID, "side-menu")
    li_elements = side_menu.find_elements(By.TAG_NAME, "li")
    main_url_list = [
        elem.find_element(By.TAG_NAME, "a").get_attribute("href")
        for elem in li_elements
    ]
    return main_url_list


def get_one_product(item: WebElement) -> Product:
    logging.info("Getting one products")
    description = item.find_element(By.CLASS_NAME, "description").text
    price = float(
        item.find_element(By.CLASS_NAME, "price").text.replace("$", "")
    )
    title = item.find_element(By.CLASS_NAME, "title").get_attribute("title")
    review_count_element = item.find_element(By.CLASS_NAME, "review-count")
    num_of_review = int(review_count_element.text.split()[0])
    rating_div = item.find_element(By.CLASS_NAME, "ratings")
    rating = len(rating_div.find_elements(By.CLASS_NAME, "ws-icon-star"))
    logging.info(
        f"Product title: {title}"
        f"  description: {description}"
        f"  rating: {rating}"
        f" Number of reviews: {num_of_review}"
    )
    return Product(
        title=title,
        description=description,
        price=price,
        rating=rating,
        num_of_reviews=num_of_review,
    )


def click_next_page(driver: WebDriver) -> None:
    try:
        next_page = driver.find_element(By.CLASS_NAME, "btn-primary")
    except NoSuchElementException:
        next_page = None

    if next_page:
        attribute = next_page.get_attribute("style")
        while attribute != "display: none;":
            next_page.click()
            sleep(0.25)
            attribute = next_page.get_attribute("style")


def get_urls_subcategories(driver: WebDriver) -> list[str] | None:
    try:
        subcategories = driver.find_elements(By.CLASS_NAME, "nav-second-level")
    except NoSuchElementException:
        subcategories = None

    if subcategories:
        ul_element = driver.find_element(By.CLASS_NAME, "nav-second-level")
        subcategory_links = ul_element.find_elements(
            By.CSS_SELECTOR, "a.nav-link.subcategory-link"
        )
        return [
            sub_link.get_attribute("href") for sub_link in subcategory_links
        ]
    else:
        return None


def parse_products_one_page(url: str) -> list:
    logging.info(f"Start parsing {url}")
    driver = get_driver()
    driver.get(url)
    result = []
    subcategories_urls = get_urls_subcategories(driver)
    click_next_page(driver)
    products_list = driver.find_elements(By.CLASS_NAME, "thumbnail")
    for item in products_list:
        product = get_one_product(item)
        result.append(product)
    logging.info(f"Finish parsing {url} num products is: {len(result)}")
    return [result, subcategories_urls]


def get_all_products() -> None:
    with webdriver.Chrome() as new_driver:
        set_driver(new_driver)
        start_url = urljoin(BASE_URL, HOME_URL)
        main_url_list = start_accept_cookies_get_list_main_url(start_url)
        item_dict = {}
        for url in main_url_list:
            item, subcategory_urls = parse_products_one_page(url)
            name = url.split("/")[-1]
            if name == "more":
                name = "home"
            item_dict.update({name: item})
            if subcategory_urls:
                for sub_url in subcategory_urls:
                    sub_item, sub_category = parse_products_one_page(sub_url)
                    sub_name = sub_url.split("/")[-1]
                    item_dict.update({sub_name: sub_item})

    for key, value in item_dict.items():
        write_csv(key + ".csv", value, PRODUCT_FIELDS)


if __name__ == "__main__":
    get_all_products()
