import csv
from dataclasses import dataclass, fields, astuple
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.webdriver import WebDriver
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


def get_price_from_cards(cards: list[WebElement]) -> list[float]:
    return [float(card.find_element(
        By.CSS_SELECTOR,
        "h4.price"
    ).text.replace("$", ""))for card in cards]


def get_rating_from_cards(cards: list[WebElement]) -> list[int]:
    return [len(card.find_elements(
        By.CSS_SELECTOR,
        "div.ratings > p:nth-child(2) > span"
    ))
        for card in cards]


def get_reviews_from_cards(cards: list[WebElement]) -> list[int]:
    return [int(card.find_element(
        By.CSS_SELECTOR,
        "div.ratings > p.float-end.review-count").text.split()[0])
        for card in cards]


def get_description_from_cards(cards: list[WebElement]) -> list[str]:
    return [card.find_element(By.CSS_SELECTOR, "div.caption > p").text for
            card in cards]


def get_title_from_cards(cards: list[WebElement]) -> list[str]:
    list_of_title = []
    for card in cards:
        href = card.find_element(
            By.CSS_SELECTOR,
            "div.caption > h4:nth-child(2) > a"
        ).get_attribute("href")
        req = requests.get(href, verify=False).content
        soup = BeautifulSoup(req, "html.parser")
        list_of_title.append(soup.select_one(
            "div.col-xl-10 > div.caption > h4.card-title"
        ).text)
    return list_of_title


def get_cards(driver: WebDriver, url: str) -> list[WebElement]:
    driver.get(url)
    try:
        button = driver.find_element(
            By.CLASS_NAME,
            "ecomerce-items-scroll-more"
        )
    except Exception:
        return driver.find_elements(By.CLASS_NAME, "card-body")
    while button.is_displayed():
        driver.execute_script("arguments[0].click();", button)
        button = driver.find_element(
            By.CLASS_NAME,
            "ecomerce-items-scroll-more"
        )
    return driver.find_elements(By.CLASS_NAME, "card-body")


def scrap(driver: WebDriver, file_url: str, url: str) -> None:
    cards = get_cards(driver, url)
    titles = get_title_from_cards(cards)
    descriptions = get_description_from_cards(cards)
    prices = get_price_from_cards(cards)
    ratings = get_rating_from_cards(cards)
    reviews = get_reviews_from_cards(cards)
    products = [
        Product(
            title=titles[i],
            description=descriptions[i],
            price=prices[i], rating=ratings[i],
            num_of_reviews=reviews[i]
        )
        for i in range(len(cards))
    ]

    with open(file_url, "w", encoding="utf-8", newline="\n") as f:
        writer = csv.writer(f)
        writer.writerow(PRODUCT_FIELDS)
        writer.writerows([astuple(product) for product in products])


def get_all_products() -> None:
    driver = webdriver.Edge()
    urls = {
        "laptops.csv":
            "https://webscraper.io/test-sites/e-commerce/more/computers/"
            "laptops",
        "tablets.csv":
            "https://webscraper.io/test-sites/e-commerce/more/computers/"
            "tablets",
        "touch.csv":
            "https://webscraper.io/test-sites/e-commerce/more/phones/touch",
        "home.csv":
            "https://webscraper.io/test-sites/e-commerce/more",
        "computers.csv":
            "https://webscraper.io/test-sites/e-commerce/more/computers",
        "phones.csv":
            "https://webscraper.io/test-sites/e-commerce/more/phones",
    }
    for key in urls:
        scrap(driver, key, urls[key])


if __name__ == "__main__":
    get_all_products()
