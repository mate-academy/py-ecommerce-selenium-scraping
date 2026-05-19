from dataclasses import astuple

from tqdm import tqdm
from selenium.common import (
    NoSuchElementException,
    ElementNotInteractableException,
    ElementClickInterceptedException
)
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from app.scrappers.banner_accept_element import banner_accept_element
from app.scrappers.one_product_scrapper import scrape_single_product


def get_product_list(driver: WebDriver, url: str) -> list:
    driver.get(url)
    banner_accept_element(driver)
    while True:
        try:
            pagination_button = driver.find_element(
                By.CLASS_NAME, "ecomerce-items-scroll-more"
            )
            ActionChains(driver).scroll_to_element(pagination_button).perform()
            pagination_button.click()
        except (
                ElementNotInteractableException,
                NoSuchElementException,
                ElementClickInterceptedException
        ):
            break

    page_products_list = driver.find_elements(
        By.CSS_SELECTOR, ".card.thumbnail"
    )
    products_obj = []
    for product in tqdm(page_products_list):
        result_product = scrape_single_product(product, driver)
        products_obj.append(result_product)
    product_tuple = [astuple(product_obj) for product_obj in products_obj]
    return product_tuple
