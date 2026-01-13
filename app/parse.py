import csv
from selenium import webdriver
from selenium.common import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec

import time
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")
COMPUTER_URL = urljoin(HOME_URL, "computers")
PHONES_URL = urljoin(HOME_URL, "phones")

URLS = [
    HOME_URL,
    COMPUTER_URL,
    COMPUTER_URL + "/laptops",
    COMPUTER_URL + "/tablets",
    PHONES_URL,
    PHONES_URL + "/touch",
]

fields = ["title", "description", "price", "rating", "num_of_reviews"]
driver = webdriver.Firefox()


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


def url_to_csv_name(url: str) -> str:
    path = urlparse(url).path.rstrip("/")

    last_part = path.split("/")[-1]

    if last_part == "more":
        return "home.csv"

    return f"{last_part}.csv"


def write_csv(filename: str, text: list) -> None:
    with open(filename, "w") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fields)
        writer.writeheader()
        writer.writerows(text)


def get_all_products() -> None:

    try:
        for url in URLS:
            result = []
            driver.get(url)
            try:
                cookie = driver.find_element(By.CLASS_NAME, "acceptCookies")
                cookie.click()
                button = driver.find_element(By.CLASS_NAME, "btn")
            except NoSuchElementException:
                button = None

            WebDriverWait(driver, 10).until(
                ec.presence_of_all_elements_located((
                    By.CLASS_NAME, "caption")))
            if button:
                while True:
                    button.click()
                    time.sleep(2)
                    try:
                        button_style = driver.find_element(
                            By.CSS_SELECTOR, "a[style]"
                        )
                    except NoSuchElementException:
                        continue
                    if button_style:
                        break
            info = driver.find_elements(By.CLASS_NAME, "caption")
            ratings = driver.find_elements(By.CLASS_NAME, "ratings")

            for element, rating in zip(info, ratings):
                title_attribute = element.find_element(By.CSS_SELECTOR, "a[title]")
                title = title_attribute.get_attribute("title")
                price = float(
                    element.find_element(
                        By.CLASS_NAME, "price"
                    ).text.replace("$", ""))
                text = element.find_element(By.TAG_NAME, "p").text

                count_reviews = rating.find_element(By.CLASS_NAME, "review-count")

                reviews = count_reviews.find_element(By.TAG_NAME, "span").text

                stars_list = rating.find_elements(By.CLASS_NAME, "ws-icon")
                stars = len(stars_list)

                product = Product(title, text, price, stars, reviews)

                result.append(
                    {"title": product.title,
                     "description": product.description,
                     "price": product.price,
                     "rating": product.rating,
                     "num_of_reviews": product.num_of_reviews
                     }
                )

            filename = url_to_csv_name(url)
            write_csv(filename, result)
    except Exception as e:
        print(e)
    finally:
        driver.quit()


if __name__ == "__main__":
    get_all_products()
