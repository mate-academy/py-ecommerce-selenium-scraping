import csv
from dataclasses import dataclass, fields, astuple
import time
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup, Tag

from selenium import webdriver
from selenium.webdriver.common.by import By # <-- Тут все правильно
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.common import (
    TimeoutException,
    ElementClickInterceptedException,
    NoSuchElementException,
)


BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL,
                   "test-sites/e-commerce/more/")
COMPUTERS_URL = urljoin(BASE_URL,
                        "test-sites/e-commerce/more/computers")
PHONES_URL = urljoin(BASE_URL,
                     "test-sites/e-commerce/more/phones")
COMPUTERS_LAPTOPS_URL = urljoin(BASE_URL,
                                "test-sites/e-commerce/more/computers/laptops")
COMPUTERS_TABLETS_URL = urljoin(BASE_URL,
                                "test-sites/e-commerce/more/computers/tablets")
PHONES_TOUCH_URL = urljoin(BASE_URL,
                           "test-sites/e-commerce/more/phones/touch")


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


PRODUCT_FIELDS = [field.name for field in fields(Product)]


def parse_product_bs4(product_tag: Tag) -> Product:

    title = product_tag.select_one(".caption a.title").get("title").strip()
    description = product_tag.select_one(".caption p.description").text.strip()
    price = float(product_tag.select_one(
        "h4.price").text.replace("$", "").strip())

    ratings_container = product_tag.select_one("div.ratings")
    star_icons = ratings_container.select("span.ws-icon.ws-icon-star")
    rating = len(star_icons)

    num_of_reviews_element = product_tag.select_one(
        ".review-count span[itemprop='reviewCount']")
    num_of_reviews = 0
    if num_of_reviews_element:
        num_of_reviews = int(num_of_reviews_element.text.strip())
    else:
        reviews_p = product_tag.select_one(".review-count")
        if reviews_p:
            num_part = reviews_p.text.strip().split(" ")[0]
            num_of_reviews = int(num_part)

    return Product(
        title=title,
        description=description,
        price=price,
        rating=rating,
        num_of_reviews=num_of_reviews,
    )


def parse_product_selenium(product_element: WebElement) -> Product:

    title = product_element.find_element(
        By.CSS_SELECTOR,
        ".caption a.title",
    ).get_attribute("title").strip()
    description = product_element.find_element(
        By.CSS_SELECTOR,
        ".caption p.description",
    ).text.strip()
    price_text = product_element.find_element(By.CSS_SELECTOR, "h4.price").text
    price = float(price_text.replace("$", "").strip())

    ratings_container = product_element.find_element(By.CLASS_NAME, "ratings")
    star_icons = ratings_container.find_elements(By.CLASS_NAME, "ws-icon-star")
    rating = len(star_icons)

    num_of_reviews_element = product_element.find_element(
        By.CSS_SELECTOR,
        ".review-count span[itemprop='reviewCount']",
    )
    num_of_reviews = 0
    if num_of_reviews_element:
        num_of_reviews = int(num_of_reviews_element.text.strip())
    else:
        reviews_p = product_element.find_element(By.CLASS_NAME, "review-count")
        if reviews_p:
            num_part = reviews_p.text.strip().split(" ")[0]
            num_of_reviews = int(num_part)

    return Product(
        title=title,
        description=description,
        price=price,
        rating=rating,
        num_of_reviews=num_of_reviews,
    )


def write_products_to_csv(products: list[Product], filename: str) -> None:

    with open(f"{filename}.csv", "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(PRODUCT_FIELDS)
        writer.writerows([astuple(product) for product in products])


def click_more_until_disabled(
        driver: webdriver.Chrome,
        button_selector: str,
) -> None:
    wait = WebDriverWait(driver, 10)

    while True:
        try:
            more_button = wait.until(
                ec.element_to_be_clickable((By.CSS_SELECTOR, button_selector))
            )

            if more_button.get_attribute("disabled"):
                print("The 'More' button has become inactive (disabled).")
                break

            driver.execute_script(
                "arguments[0].scrollIntoView(true);",
                more_button,
            )
            time.sleep(0.5)

            more_button.click()

            time.sleep(2)

        except TimeoutException:
            print("The 'More' button was not found "
                  "or is no longer clickable (timed out).")
            break
        except ElementClickInterceptedException:
            print("Click on 'More' button intercepted"
                  " by another element. Click attempt via JavaScript.")
            driver.execute_script("arguments[0].click();", more_button)
            time.sleep(2)
        except NoSuchElementException:
            print("The 'More' button has disappeared.")
            break
        except Exception as e:
            print(f"Unexpected error when clicking 'More': {e}")
            break


def get_products_for_static_page(url: str, filename: str) -> None:

    response = requests.get(url)
    response.raise_for_status()
    soup = BeautifulSoup(response.content, "html.parser")
    products_html = soup.select(".product-wrapper.card-body")

    parsed_products = []
    for product_tag in products_html:
        parsed_products.append(parse_product_bs4(product_tag))

    write_products_to_csv(parsed_products, filename)


def get_products_for_dynamic_page(
        driver: webdriver.Chrome,
        url: str,
        filename: str,
        button_selector: str,
) -> None:

    driver.get(url)

    WebDriverWait(driver, 10).until(
        ec.presence_of_element_located(
            (By.CSS_SELECTOR, ".product-wrapper.card-body")
        )
    )

    click_more_until_disabled(driver, button_selector)

    products_data = []
    product_elements = driver.find_elements(
        By.CSS_SELECTOR,
        ".product-wrapper.card-body",
    )
    for product_element in product_elements:
        products_data.append(parse_product_selenium(product_element))

    write_products_to_csv(products_data, filename)


def get_all_products() -> None:
    chrome_options = webdriver.ChromeOptions()
    driver = webdriver.Chrome(options=chrome_options)

    try:

        get_products_for_static_page(HOME_URL, "home")
        get_products_for_static_page(COMPUTERS_URL, "computers")
        get_products_for_static_page(PHONES_URL, "phones")

        get_products_for_dynamic_page(
            driver,
            COMPUTERS_LAPTOPS_URL,
            "laptops",
            ".ecomerce-items-scroll-more",
        )
        get_products_for_dynamic_page(
            driver,
            COMPUTERS_TABLETS_URL,
            "tablets",
            ".ecomerce-items-scroll-more",
        )
        get_products_for_dynamic_page(
            driver,
            PHONES_TOUCH_URL,
            "touch",
            ".ecomerce-items-scroll-more",
        )

    finally:
        driver.quit()


if __name__ == "__main__":
    get_all_products()