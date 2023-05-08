import csv
import time
from selenium import webdriver
from selenium.common import (
    NoSuchElementException,
    ElementNotInteractableException,
    ElementClickInterceptedException
)
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup, Tag
from dataclasses import dataclass, fields
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service


URLS = {
    "home": "https://webscraper.io/test-sites/"
    "e-commerce/more",

    "phones": "https://webscraper.io/test-sites/"
    "e-commerce/more/phones",

    "touch": "https://webscraper.io/test-sites/"
    "e-commerce/more/phones/touch",

    "computers": "https://webscraper.io/test-sites/"
    "e-commerce/more/computers",

    "tablets": "https://webscraper.io/test-sites/"
    "e-commerce/more/computers/tablets",

    "laptops": "https://webscraper.io/test-sites/"
    "e-commerce/more/computers/laptops",
}


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


PRODUCT_FIELDS = [field.name for field in fields(Product)]


def get_single_product(product_tag: Tag) -> Product:
    try:
        rating = int(product_tag.select_one("p[data-rating]")["data-rating"])
    except TypeError:
        rating = 5

    return Product(
        title=product_tag.select_one(".title").attrs["title"],
        description=product_tag.select_one(".description").text.replace(
            "\xa0", " "
        ),
        price=float(product_tag.select_one(".price").text.replace("$", "")),
        rating=rating,
        num_of_reviews=int(product_tag.select_one(
            ".ratings > p.pull-right"
        ).text.split()[0]),
    )


def click_cookie(driver: webdriver) -> None:
    try:
        cookies = driver.find_element(By.CLASS_NAME, "acceptCookies")
        cookies.click()
        time.sleep(1)
    except NoSuchElementException:
        pass


def click_more_button(driver: webdriver) -> None:
    while True:
        try:
            more_button = driver.find_element(
                By.CLASS_NAME, "ecomerce-items-scroll-more"
            )
            more_button.click()
        except (
                ElementNotInteractableException,
                NoSuchElementException,
                ElementClickInterceptedException
        ):
            break


def get_all_products_from_one_page(
        driver: webdriver,
        url: str,
        filename: str
) -> None:
    driver.get(url)
    click_cookie(driver)
    click_more_button(driver)
    soup = BeautifulSoup(driver.page_source, "html.parser")
    product_soup = soup.select("div.thumbnail")
    with open(f"{filename}.csv", "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=PRODUCT_FIELDS)
        writer.writeheader()

        for product in product_soup:
            data = get_single_product(product)
            writer.writerow(data.__dict__)


def get_driver() -> webdriver:
    service = Service("/usr/local/bin/chromedriver")
    options = Options().add_argument("headless")
    driver = webdriver.Chrome(service=service, options=options)
    return driver


def get_all_products() -> None:
    driver = get_driver()
    for filename, url in URLS.items():
        get_all_products_from_one_page(driver, url, filename)


if __name__ == "__main__":
    get_all_products()
