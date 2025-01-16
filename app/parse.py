import csv
from dataclasses import dataclass
from time import sleep
from urllib.parse import urljoin
from selenium import webdriver
from selenium.common import NoSuchElementException
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
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


def get_product(item: WebElement) -> Product:
    return Product(
        title=item.find_element(By.CLASS_NAME, "title").get_attribute("title"),
        description=item.find_element(
            By.CLASS_NAME,
            "description"
        ).text,
        price=float(
            item.find_element(
                By.CLASS_NAME,
                "price")
            .text.replace("$", "")
        ),
        rating=sum(
            1 for star in item.find_elements(
                By.CLASS_NAME,
                "ws-icon-star"
            )
        ),
        num_of_reviews=int(
            item.find_element(
                By.CLASS_NAME,
                "review-count"
            ).text.split()[0])
    )


def get_products(
        home_url: str,
        page: str,
        driver: WebDriver()
) -> list[Product]:
    url = urljoin(home_url, page)
    driver.get(url)
    while True:
        driver.execute_script(
            "window.scrollTo(0, document.body.scrollHeight);"
        )
        try:
            button = driver.find_element(
                By.CLASS_NAME,
                "ecomerce-items-scroll-more"
            )
        except NoSuchElementException:
            break
        sleep(0.2)
        if not button.is_displayed():
            break
        button.click()
        sleep(2)
    items = driver.find_elements(By.CLASS_NAME, "card")
    products = [get_product(item) for item in items]
    return products


def write_to_file(products: list[Product], output_file: str) -> None:
    try:
        with open(output_file, "a", newline="") as csvfile:
            fieldnames = [
                "title",
                "description",
                "price",
                "rating",
                "num_of_reviews"
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for product in products:
                writer.writerow({
                    "title": product.title,
                    "description": product.description,
                    "price": product.price,
                    "rating": product.rating,
                    "num_of_reviews": product.num_of_reviews
                })
    except (PermissionError, IOError) as e:
        print("Can't save quotes to file")
        print(e)


def get_all_products() -> None:
    with webdriver.Chrome() as driver:
        home = get_products(HOME_URL, "", driver)
        computers = get_products(HOME_URL, "computers", driver)
        phones = get_products(HOME_URL, "phones", driver)
        laptops = get_products(HOME_URL, "computers/laptops", driver)
        tablets = get_products(HOME_URL, "computers/tablets", driver)
        touch = get_products(HOME_URL, "phones/touch", driver)
    write_to_file(home, "home.csv")
    write_to_file(computers, "computers.csv")
    write_to_file(phones, "phones.csv")
    write_to_file(laptops, "laptops.csv")
    write_to_file(tablets, "tablets.csv")
    write_to_file(touch, "touch.csv")


if __name__ == "__main__":
    get_all_products()
