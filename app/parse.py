from dataclasses import dataclass
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.select import Select


BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")
COMPUTERS_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/computers/")
LAPTOPS_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/computers/laptops/")
TABLETS_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/computers/tablets/")
PHONES_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/phones/")
TORCHES_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/phones/touch/")


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int
    additional_info: {}


def parse_colors(driver) -> list:
    colors_product = []
    color_check = driver.find_elements(By.CSS_SELECTOR, "select[aria-label='color']")
    if color_check:
        colors = Select(color_check[0]).options
        for color in colors[1:]:
            colors_product.append(color.text)
    return colors_product


def parse_hdd_prices(driver) -> dict:
    hdd_prices = {}
    swatches = driver.find_elements(By.CLASS_NAME, "swatches")
    if swatches:
        buttons = swatches[0].find_elements(By.TAG_NAME, "button")
        for button in buttons:
            button.click()
            price = float(
                driver.find_element(By.CLASS_NAME, "price").text.replace("$", "")
            )
            hdd_prices[button.get_property("value")] = price
    return hdd_prices


def parse_additional_info(product_soup: BeautifulSoup) -> tuple[dict]:
    detail_url = urljoin(BASE_URL, product_soup.select_one(".title")["href"])
    driver = webdriver.Chrome()
    driver.get(detail_url)

    cookies = driver.find_elements(By.CLASS_NAME, "acceptContainer")

    if cookies:
        button = cookies[0].find_element(By.TAG_NAME, "button")
        button.click()
        print("click")

    colors_product = parse_colors(driver)

    hdd_prices = parse_hdd_prices(driver)

    driver.close()

    return hdd_prices, colors_product


def parse_single_products(soup: BeautifulSoup) -> Product:
    hdd_and_prices = parse_additional_info(soup)
    additional_info = {"hdd_prices": hdd_and_prices[0]}
    if hdd_and_prices[1]:
        additional_info.update({"colors": hdd_and_prices[1]})

    return Product(
        title=soup.select_one(".title").text,
        description=soup.select_one(".description").text,
        price=float(soup.select_one(".price").text.replace("$", "")),
        rating=len(soup.select(".ws-icon-star")),
        num_of_reviews=int(soup.select_one(".review-count").text.split(" ")[0]),
        additional_info=additional_info,
    )


def get_single_page_products(page_soup: BeautifulSoup) -> list[Product]:
    products = page_soup.select(".product-wrapper")
    return [parse_single_products(product) for product in products]


def get_all_products(url) -> None:
    page = requests.get(url).content
    soup = BeautifulSoup(page, "html.parser")
    first_page_parse = get_single_page_products(soup)

    for i in first_page_parse:
        print(i)


if __name__ == "__main__":
    get_all_products(HOME_URL)
