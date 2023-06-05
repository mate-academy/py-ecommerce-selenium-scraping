import time
from dataclasses import dataclass
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from selenium.common import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from tqdm import tqdm
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/phones/touch")


class Driver:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not isinstance(Driver._instance, Driver):
            Driver._instance = object.__new__(Driver)
        return Driver._instance

    def __init__(self):
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        self.driver = webdriver.Chrome(options=chrome_options)

    def closed(self):
        self.driver.quit()


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


def click_button_more(browser: Driver):
    try:
        # initial_num_products = len(
        #     browser.driver.find_elements(By.CSS_SELECTOR, ".thumbnail")
        # )
        button = browser.driver.find_element(
            By.CSS_SELECTOR,
            "a.ecomerce-items-scroll-more",
        )
        browser.driver.execute_script(
            "arguments[0].scrollIntoView(true);", button
        )
        browser.driver.execute_script("arguments[0].click();", button)
        wait = WebDriverWait(browser.driver, 10)
        g = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".thumbnail")))
        print(g)

    except NoSuchElementException:
        return None


def click_side_bar_button(browser: Driver):
    all_path = []
    try:
        button = browser.driver.find_element(
            By.CSS_SELECTOR,
            "a.category-link",
        )
        all_path.append(button.get_attribute("href"))
        button.click()
    except NoSuchElementException:
        pass


def parse_all_products() -> list[Product]:
    url = HOME_URL
    browser = Driver()
    browser.driver.get(url)
    click_button_more(browser)
    updated_html = browser.driver.page_source

    soup = BeautifulSoup(updated_html, "html.parser")
    products = soup.select(".thumbnail")

    return [
        Product(
            title=product.select_one(".title")["title"].strip(),
            description=product.select_one(".description").text,
            price=float(
                product.select_one("div.caption > h4").text.replace("$", "")
            ),
            rating=len(product.select("div.ratings > p > span")),
            num_of_reviews=int(
                product.select_one("div.ratings > p.pull-right").text.split(
                    " "
                )[0]
            ),
        )
        for product in products
    ]


def get_all_products() -> None:
    pass
    # url = HOME_URL
    # browser = Driver()
    # browser.driver.get(url)
    # parse_all_products(browser)


if __name__ == "__main__":
    print(len(parse_all_products()))
