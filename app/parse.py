import csv
import time
from dataclasses import dataclass, fields, astuple
from urllib.parse import urljoin

from selenium import webdriver
from selenium.common import NoSuchElementException
from selenium.webdriver.common.by import By


BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")
COMPUTERS_URL = urljoin(HOME_URL, "computers/")
LAPTOPS_URL = urljoin(COMPUTERS_URL, "laptops")
TABLETS_URL = urljoin(COMPUTERS_URL, "tablets")
PHONES_URL = urljoin(HOME_URL, "phones/")
TOUCH_URL = urljoin(PHONES_URL, "touch")


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


PRODUCT_FIELDS = [field.name for field in fields(Product)]

driver = webdriver.Chrome()


def click_accept_cookie() -> None:
    driver.get(HOME_URL)
    try:
        button = driver.find_element(By.CLASS_NAME, "t-acceptAllButton")
        button.click()
        time.sleep(1)
    except NoSuchElementException:
        pass


def get_product(url: str) -> list[Product]:
    driver.get(url)

    try:
        more_button = driver.find_element(
            By.CLASS_NAME, "ecomerce-items-scroll-more"
        )
        while more_button.is_displayed():
            driver.execute_script(
                "arguments[0].scrollIntoView({block: 'center'});",
                more_button
            )
            more_button.click()
            time.sleep(1)
    except NoSuchElementException:
        pass

    elements = driver.find_elements(By.CLASS_NAME, "card-body")
    result = []
    for element in elements:
        result.append(
            Product(
                title=(
                    element
                    .find_element(By.CLASS_NAME, "title")
                    .get_attribute("title")
                ),
                description=element.find_element(
                    By.CLASS_NAME, "description"
                ).text,
                price=float(
                    element.find_element(
                        By.CLASS_NAME, "price").text[1:]
                ),
                rating=len(
                    element.find_elements(
                        By.CSS_SELECTOR, ".ratings .ws-icon-star"
                    )
                ),
                num_of_reviews=int(
                    element.find_element(
                        By.CSS_SELECTOR, ".ratings span[itemprop]"
                    ).text
                )
            )
        )

    return result


def write_to_csv(products: list[Product], file_name: str) -> None:
    with open(file_name, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(PRODUCT_FIELDS)
        writer.writerows([astuple(product) for product in products])


def get_all_products() -> None:
    try:
        click_accept_cookie()
        write_to_csv(get_product(HOME_URL), "home.csv")
        write_to_csv(get_product(COMPUTERS_URL), "computers.csv")
        write_to_csv(get_product(LAPTOPS_URL), "laptops.csv")
        write_to_csv(get_product(TABLETS_URL), "tablets.csv")
        write_to_csv(get_product(PHONES_URL), "phones.csv")
        write_to_csv(get_product(TOUCH_URL), "touch.csv")
    finally:
        driver.quit()


if __name__ == "__main__":
    get_all_products()
