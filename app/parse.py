import csv
from dataclasses import dataclass
from time import sleep
from urllib.parse import urljoin
from selenium import webdriver
from selenium.common import NoSuchElementException
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup


BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")
URLS = [
    (HOME_URL, "home"),
    (urljoin(HOME_URL, "computers"), "computers"),
    (urljoin(HOME_URL, "computers/laptops"), "laptops"),
    (urljoin(HOME_URL, "computers/tablets"), "tablets"),
    (urljoin(HOME_URL, "phones/"), "phones"),
    (urljoin(HOME_URL, "phones/touch"), "touch")
]


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


def get_content(driver, button=None):
    try:
        driver.find_element(By.CLASS_NAME, "acceptCookies").click()
    except NoSuchElementException:
        pass
    try:
        button = driver.find_element(
            By.CLASS_NAME, "ecomerce-items-scroll-more"
        )
    except NoSuchElementException:
        pass
    if button is not None:
        while button.is_displayed():
            button.click()
            sleep(0.5)
    return driver.page_source


def parse_one_item(item):
    return Product(
        title=item.select_one(".caption > h4:nth-of-type(2)").text,
        description=item.select_one(".description").text,
        price=float(item.select_one(".caption > h4").text.replace("$", "")),
        rating=len(item.select(".glyphicon")),
        num_of_reviews=int(item.select_one(".ratings > p").text.split()[0])
    )


def get_all_products() -> None:
    driver = webdriver.Chrome()

    for url, name in URLS:
        driver.get(url)
        content = get_content(driver)
        soup = BeautifulSoup(content, "html.parser")
        items = soup.select(".thumbnail")
        filename = f"{name}.csv"

        with open(filename, "w") as file:
            writer = csv.writer(file)
            writer.writerow(["title", "description", "price", "rating", "num_of_reviews"])
            for item in items:
                prod_ins = parse_one_item(item)
                writer.writerow(tuple(prod_ins.__dict__.values()))


if __name__ == "__main__":
    get_all_products()
