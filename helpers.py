import time

from scrapy import Selector
from selenium.common import ElementNotInteractableException
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement

from app.parse import Product


def parse_single_product(product: Selector) -> Product:
    payload = {
        "title": product.css(".title::attr(title)").get(),
        "description": product.css(".description::text").get(),
        "price": float(product.css(".price::text").get().replace("$", "")),
        "rating": int(product.css("p[data-rating]::attr(data-rating)").get()),
        "num_of_reviews": int(
            product.css(".ratings > p.pull-right::text"
                        ).get().split()[0]),
    }
    return Product(**payload)


def parse_single_product_with_selenium(product: WebDriver) -> Product:
    payload = {
        "title": product.find_element(
            By.CLASS_NAME, "title"
        ).get_attribute("title"),
        "description": product.find_element(By.CLASS_NAME, "description").text,
        "price": float(product.find_element(By.CLASS_NAME,
                                            "price"
                                            ).text.replace("$", "")),
        "rating": len(product.find_elements(By.CLASS_NAME, "glyphicon-star")),
        "num_of_reviews": int(product.find_element(By.CSS_SELECTOR,
                                                   ".ratings > p.pull-right"
                                                   ).text.split()[0]),
    }
    return Product(**payload)


def ajax_pagination(url: str, driver: WebDriver) -> [WebElement]:
    driver.get(url)

    if driver.find_element(By.CLASS_NAME, "acceptCookies"):
        driver.find_element(By.CLASS_NAME, "acceptCookies").click()
    button = driver.find_element(By.CLASS_NAME, "ecomerce-items-scroll-more")
    while button:
        try:
            button.click()
            time.sleep(1)
        except ElementNotInteractableException:
            break
    time.sleep(1)
    products = driver.find_elements(By.CLASS_NAME, "thumbnail")
    return products
