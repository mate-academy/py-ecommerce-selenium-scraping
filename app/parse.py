import csv
import time
from dataclasses import dataclass, fields, astuple
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import (
    NoSuchElementException,
    ElementClickInterceptedException, ElementNotInteractableException
)
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


BASE_URL = "https://webscraper.io/"
PRODUCT_PAGES = {
    "home": urljoin(BASE_URL, "test-sites/e-commerce/more/"),
    "computers": urljoin(BASE_URL, "test-sites/e-commerce/static/computers/"),
    "laptops": urljoin(BASE_URL, "test-sites/e-commerce/static/computers/laptops"),
    "tablets": urljoin(BASE_URL, "test-sites/e-commerce/static/computers/tablets"),
    "phones": urljoin(BASE_URL, "test-sites/e-commerce/static/phones"),
    "touch": urljoin(BASE_URL, "test-sites/e-commerce/static/phones/touch")
}

_driver: WebDriver | None = None


def get_driver() -> WebDriver:
    return _driver

def set_driver(new_driver: WebDriver) -> None:
    global _driver
    _driver = new_driver


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int
    additional_info: dict


PRODUCT_FIELDS = [field.name for field in fields(Product)]


def close_cookie_banner():
    driver = get_driver()
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "cookieBanner"))
        )
        cookie_button = driver.find_element(
            By.ID, "cookieBanner"
        ).find_element(By.TAG_NAME, "button"
                       )

        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "cookieBanner"))
        )

        driver.execute_script("arguments[0].click();", cookie_button)
        print("Cookie banner closed successfully.")
    except (NoSuchElementException, ElementNotInteractableException) as e:
        print("Cookie banner not interactable or not present:", e)


def parse_hdd_block_prices(product_soup: BeautifulSoup) -> dict[str, float]:
    title_elem = product_soup.select_one(".title")
    if title_elem and "href" in title_elem.attrs:
        detailed_url = urljoin(BASE_URL, title_elem["href"])
    else:
        return {}

    driver = get_driver()
    driver.get(detailed_url)
    close_cookie_banner()

    prices = {}
    swatches = driver.find_element(By.CLASS_NAME, "swatches")
    buttons = swatches.find_elements(By.TAG_NAME, "button")
    for button in buttons:
        if not button.get_property("disabled"):
            try:
                button.click()
            except ElementClickInterceptedException:
                close_cookie_banner()
                button.click()
            prices[button.get_property("value")] = float(driver.find_element(
                By.CLASS_NAME, "price"
            ).text.replace("$", ""))
    return prices


def parse_single_product(product_soup: BeautifulSoup) -> Product:
    hdd_prices = parse_hdd_block_prices(product_soup)

    num_of_reviews_elem = product_soup.select_one(".ratings > p.pull-right")
    num_of_reviews = int(
        num_of_reviews_elem.text.split()[0]
    ) if num_of_reviews_elem else 0

    return Product(
        title=product_soup.select_one(".title")["title"],
        description=product_soup.select_one(".description").text,
        price=float(product_soup.select_one(".price").text.replace("$", "")),
        rating=int(product_soup.select_one("p[data-rating]")["data-rating"]),
        num_of_reviews=num_of_reviews,
        additional_info={"hdd_prices": hdd_prices},
    )

def get_num_pages(page_soup: BeautifulSoup) -> int:
    pagination = page_soup.select_one(".pagination")
    if pagination is None:
        return 1
    return int(pagination.select("li")[-2].text)


def get_single_page_products(page_soup: BeautifulSoup) -> [Product]:
    products = page_soup.select(".thumbnail")
    return [parse_single_product(product_soup) for product_soup in products]


def scrape_page(url: str, page_name: str) -> [Product]:
    driver = get_driver()
    driver.get(url)
    time.sleep(2)

    products = []
    while True:
        page_soup = BeautifulSoup(driver.page_source, "html.parser")
        products.extend(get_single_page_products(page_soup))

        more_button = driver.find_elements(By.CLASS_NAME, "btn-more")
        if more_button:
            more_button[0].click()
            time.sleep(2)
        else:
            break

    return products


def write_products_to_csv(products: [Product], filename: str) -> None:
    with open(filename, "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(PRODUCT_FIELDS)
        writer.writerows([astuple(product) for product in products])


def get_all_products() -> None:
    for page_name, url in PRODUCT_PAGES.items():
        products = scrape_page(url, page_name)
        write_products_to_csv(products, f"{page_name}.csv")


def main():
    with webdriver.Chrome() as new_driver:
        set_driver(new_driver)
        get_all_products()


if __name__ == "__main__":
    main()
