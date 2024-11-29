import csv
from dataclasses import dataclass
from typing import List
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common import NoSuchElementException, TimeoutException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
import selenium.webdriver.support.expected_conditions as expected_conditions

from selenium.webdriver.support.wait import WebDriverWait

BASE_URL = "https://webscraper.io/"


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


def write_goods_to_csv(goods: List[Product], file_name: str) -> None:
    with open(f"{file_name}.csv", "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["title",
                         "description",
                         "price",
                         "rating",
                         "num_of_reviews"])
        for good in goods:
            writer.writerow(
                [
                    good.title,
                    good.description,
                    good.price,
                    good.rating,
                    good.num_of_reviews,
                ]
            )


def fetch_html(url: str) -> str:
    response = requests.get(url)
    response.raise_for_status()
    return response.text


def parse_products(html: str) -> List[Product]:
    html = html.encode("utf-8").decode("utf-8")
    soup = BeautifulSoup(html, "html.parser")
    products = soup.select(".thumbnail")
    return [parse_single_home_product(product) for product in products]


def get_product_rating(soup: BeautifulSoup) -> int:
    rating_tag = soup.select_one("p[data-rating]")
    if rating_tag:
        return int(rating_tag["data-rating"])
    stars = soup.select(".ws-icon-star")
    return len(stars) if stars else 0


def parse_single_home_product(product_html: str) -> Product:
    soup = BeautifulSoup(str(product_html), "html.parser")
    title = soup.select_one(".title")["title"]
    description = (soup.select_one(".card-text")
                   .text.strip().replace("\xa0", " "))
    price = float(soup.select_one(".price").text[1:])
    review_tag = soup.select_one(".review-count")
    num_of_reviews = int(review_tag.get_text(strip=True).split()[0])
    rating = get_product_rating(soup)
    return Product(
        title=title,
        description=description,
        price=price,
        rating=rating,
        num_of_reviews=num_of_reviews,
    )


def get_products_from_page(url: str) -> List[Product]:
    html = fetch_html(url)
    return parse_products(html)


def get_full_content_page(driver: webdriver.Chrome, url: str) -> str:
    driver.get(url)

    try:
        cookie_button = driver.find_element(By.CLASS_NAME, "acceptCookies")
        cookie_button.click()
    except NoSuchElementException:
        pass

    while True:
        try:
            button = WebDriverWait(driver, 15).until(
                expected_conditions.element_to_be_clickable(
                    (By.CLASS_NAME, "ecomerce-items-scroll-more")
                )
            )
            if button.is_displayed() and button.is_enabled():
                try:
                    (ActionChains(driver)
                     .move_to_element(button).click().perform())
                except Exception as e:
                    print(f"Error: {e}")
                    break
            else:
                break
        except TimeoutException:
            break
    return driver.page_source


def get_products_from_category(category_path: str) -> List[Product]:
    url = urljoin(BASE_URL, category_path)
    driver = webdriver.Chrome()
    try:
        html = get_full_content_page(driver, url)
    finally:
        driver.quit()

    return parse_products(html)


def get_products_from_home_page() -> List[Product]:
    return get_products_from_category("test-sites/e-commerce/more/")


def get_all_products() -> None:
    categories = {
        "home":
            "test-sites/e-commerce/more",
        "computers":
            "https://webscraper.io/test-sites/e-commerce/more/computers",
        "laptops":
            "test-sites/e-commerce/more/computers/laptops",
        "tablets":
            "test-sites/e-commerce/more/computers/tablets",
        "phones":
            "test-sites/e-commerce/more/phones",
        "touch":
            "test-sites/e-commerce/more/phones/touch",
    }
    for name, path in categories.items():
        products = get_products_from_category(path)
        write_goods_to_csv(products, f"{name}")


if __name__ == "__main__":
    get_all_products()
