from dataclasses import dataclass
from time import sleep
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.select import Select
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from tqdm import tqdm

BASE_URL = "https://webscraper.io"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more")
COMPUTERS_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/computers")
LAPTOPS_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/computers/laptops")
TABLETS_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/computers/tablets")
PHONES_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/phones")
TORCHES_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/phones/touch")
HOME_PAGE_PRODUCTS_CSV_PATH = "home.csv"
COMPUTERS_PAGE_PRODUCTS_CSV_PATH = "computers.csv"
LAPTOPS_PAGE_PRODUCTS_CSV_PATH = "laptops.csv"
TABLETS_PAGE_PRODUCTS_CSV_PATH = "tablets.csv"
PHONES_PAGE_PRODUCTS_CSV_PATH = "phones.csv"
TOUCH_PAGE_PRODUCTS_CSV_PATH = "touch.csv"

OPTIONS_CHROME = webdriver.ChromeOptions()
OPTIONS_CHROME.add_argument("--window-size=1920,1080")
OPTIONS_CHROME.add_argument("--headless")


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


def click_accept_cookies(driver: webdriver.Chrome) -> None:
    cookies = driver.find_elements(By.CLASS_NAME, "acceptContainer")

    if cookies:
        button = cookies[0].find_element(By.TAG_NAME, "button")
        WebDriverWait(driver, 1).until(EC.element_to_be_clickable(button))
        button.click()


def parse_additional_info(product_soup: BeautifulSoup) -> tuple[dict]:
    detail_url = urljoin(BASE_URL, product_soup.select_one(".title")["href"])
    driver = webdriver.Chrome(options=OPTIONS_CHROME)
    driver.get(detail_url)

    click_accept_cookies(driver)

    colors_product = parse_colors(driver)
    hdd_prices = parse_hdd_prices(driver)

    driver.close()

    return hdd_prices, colors_product


def parse_single_products(soup: BeautifulSoup) -> Product:
    info = parse_additional_info(soup)

    additional_info = {}
    if info[0]:
        additional_info.update({"hdd_prices": info[0]})
    if info[1]:
        additional_info.update({"colors": info[1]})

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
    return [
        parse_single_products(product)
        for product in tqdm(products, desc="Parser products")
    ]


def click_all_button_more(driver: webdriver.Chrome) -> None:
    button = driver.find_elements(By.CLASS_NAME, "ecomerce-items-scroll-more")
    if button:
        button = button[0]
        while not button.get_attribute("style"):
            button.click()
            sleep(0.1)


def get_all_products(url) -> None:
    with webdriver.Chrome(options=OPTIONS_CHROME) as driver:
        driver.get(url)
        click_accept_cookies(driver)
        click_all_button_more(driver)
        html = driver.page_source
        soup = BeautifulSoup(html, "html.parser")
        parse = get_single_page_products(soup)

    for i in parse:
        print(i)


def main():
    get_all_products(TORCHES_URL)


if __name__ == "__main__":
    main()
