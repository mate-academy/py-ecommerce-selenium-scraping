import csv
import time
import types
from dataclasses import dataclass
from typing import Optional, Type
from urllib.parse import urljoin

from selenium import webdriver
from selenium.common import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


PRODUCT_FIELDS = [
    "title", "description", "price", "rating", "num_of_reviews"
]


class WebDriver:
    def __init__(self, driver: webdriver) -> None:
        self.driver = driver

    def __enter__(self) -> webdriver:
        return self.driver

    def __exit__(
            self,
            exc_type: Optional[Type[BaseException]],
            exc_val: Optional[BaseException],
            exc_tb: Optional[types.TracebackType]
    ) -> None:
        self.driver.quit()


def set_product(driver: webdriver) -> Product:
    return Product(
        title=driver.find_element(
            By.CLASS_NAME, "title"
        ).get_attribute("title"),
        description=driver.find_element(By.CLASS_NAME, "description").text,
        price=float(driver.find_element(By.CLASS_NAME, "price").text[1:]),
        rating=len(driver.find_elements(
            By.CSS_SELECTOR, ".ratings > p > span.ws-icon-star"
        )),
        num_of_reviews=int(driver.find_element(
            By.CSS_SELECTOR, ".ratings > p.review-count"
        ).text.split()[0])
    )


def click_button_more(driver: webdriver) -> None:
    while True:
        try:
            more_button = WebDriverWait(driver, 1).until(
                ec.element_to_be_clickable((
                    By.CSS_SELECTOR, ".ecomerce-items-scroll-more"
                ))
            )
            more_button.click()
            time.sleep(0.5)
        except TimeoutException:
            break


def scrape_page_product(driver: webdriver, link: str) -> [Product]:
    driver.get(link)
    time.sleep(1)
    click_cookie(driver)
    click_button_more(driver)
    cards = driver.find_elements(
        By.CSS_SELECTOR, "div.col-md-4.col-xl-4.col-lg-4"
    )
    all_products = [set_product(card) for card in cards]
    # for card in cards:
    #     product = set_product(card)
    #     print(product)
    return all_products


def click_cookie(driver: webdriver) -> None:
    try:
        cookie = driver.find_element(
            By.CSS_SELECTOR,
            "#cookieBanner > div.acceptContainer > a.acceptCookies"
        )
        if cookie.is_displayed():
            cookie.click()
            print("clicked")
    except NoSuchElementException:
        print("No cookie")


def get_link_page(driver: webdriver) -> {str: str}:
    navigations = driver.find_elements(
        By.CSS_SELECTOR, "#side-menu > li.nav-item > a.nav-link"
    )
    all_link = {}
    links = {nav.text: nav.get_attribute("href") for nav in navigations}
    for name, link in links.items():
        all_link[name] = link
        driver.get(link)
        second_navigations = driver.find_elements(
            By.CSS_SELECTOR,
            "ul.nav-second-level > li.nav-item > a.subcategory-link"
        )
        for nav in second_navigations:
            all_link[nav.text] = nav.get_attribute("href")
    return all_link


def scrape_all_links(driver: webdriver) -> None:
    driver.get(HOME_URL)
    for name, link in get_link_page(driver).items():
        page_product = scrape_page_product(driver, link)
        write_to_csv(name, page_product)


def write_to_csv(
        page_name: str,
        product: [Product],
) -> None:
    with open(
            f"{page_name}.csv",
            "w",
            newline="",
            encoding="UTF-8"
    ) as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(PRODUCT_FIELDS)
        for prod in product:
            row_data = [getattr(prod, field) for field in PRODUCT_FIELDS]
            writer.writerow(row_data)


def get_all_products() -> None:
    with WebDriver(webdriver.Chrome()) as driver:
        scrape_all_links(driver)


if __name__ == "__main__":
    get_all_products()
