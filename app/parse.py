import csv
import time
from dataclasses import dataclass, fields, astuple
from typing import List
from urllib.parse import urljoin

from selenium import webdriver
from selenium.common import NoSuchElementException, ElementNotInteractableException
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.remote.webelement import WebElement

options = Options()

options.add_argument("--headless")
options.add_argument("--disable-gpu")


BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")

HOME_URL_FOR_PARCE = urljoin(BASE_URL, "test-sites/e-commerce/more")

COMPUTERS_URL = urljoin(HOME_URL, "computers")
LAPTOPS_URL = urljoin(HOME_URL, "computers/laptops")
TABLETS_URL = urljoin(HOME_URL, "computers/tablets")

PHONES_URL = urljoin(HOME_URL, "phones")
TOUCH_PHONES_URL = urljoin(HOME_URL, "phones/touch")

ALL_LINKS = [
    HOME_URL_FOR_PARCE, COMPUTERS_URL, LAPTOPS_URL, TABLETS_URL, PHONES_URL, TOUCH_PHONES_URL
]


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


def get_single_product(product: WebElement) -> Product:
    title = product.find_element(By.CLASS_NAME, "title").get_attribute("title")
    description = product.find_element(By.CLASS_NAME, "description").text
    price = float(product.find_element(By.CLASS_NAME, "price").text.replace("$", ""))
    rating = len(product.find_elements(By.CLASS_NAME, "ws-icon-star"))
    num_of_reviews = int(product.find_element(By.CLASS_NAME, "review-count").text.split(" ")[0])

    product = Product(
        title=title,
        description=description,
        price=price,
        rating=rating,
        num_of_reviews=num_of_reviews
    )

    return product


def get_page_products(link: str, start: int = 1) -> List[Product]:
    with webdriver.Chrome() as driver:
        driver.get(link)

        try:
            driver.find_element(By.ID, "closeCookieBanner").click()
        except NoSuchElementException:
            pass

        more = True

        page_products = []

        while more is not None:
            first_xpath = f"/html/body/div[1]/div[3]/div/div[2]/div/div[{start}]"

            try:
                web_product = driver.find_element(By.XPATH, first_xpath)
                product = get_single_product(web_product)
                page_products.append(product)
            except NoSuchElementException:
                time.sleep(2.0)
                try:
                    more = driver.find_element(
                        By.CLASS_NAME, "ecomerce-items-scroll-more"
                    )
                except NoSuchElementException as e:
                    more = None
                else:
                    try:
                        more.click()
                        time.sleep(1.5)
                    except ElementNotInteractableException as e:
                        break
                    else:
                        continue
            else:
                start += 1

        return page_products


def get_all_products() -> None:

    for link in ALL_LINKS:
        file_name = f"{link.split('/')[-1]}.csv"
        if file_name == "more.csv":
            file_name = "home.csv"
        page_products = get_page_products(link)

        with open(file_name, "w") as f:
            writer = csv.writer(f)
            writer.writerow([field.name for field in fields(Product)])
            writer.writerows([astuple(product) for product in page_products])


if __name__ == "__main__":
    get_all_products()
