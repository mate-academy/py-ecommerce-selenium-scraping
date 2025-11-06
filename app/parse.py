from dataclasses import dataclass, fields
from urllib.parse import urljoin
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
import csv


BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")
PARSE_DATA = {
    "home": HOME_URL,
    "computers": urljoin(HOME_URL, "computers"),
    "laptops": urljoin(HOME_URL, "computers/laptops"),
    "tablets": urljoin(HOME_URL, "computers/tablets"),
    "phones": urljoin(HOME_URL, "phones"),
    "touch": urljoin(HOME_URL, "phones/touch")
}


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int
    additional_info: dict


class Browser():
    def __init__(self) -> None:
        self.driver = webdriver.Edge()

    def open_page(self, page_link: str) -> None:
        self.driver.get(page_link)

    def close(self) -> None:
        self.driver.quit()


def parse_buttons(browser: Browser, product: WebElement) -> dict | None:
    result = None
    swatches = product.find_element(By.CLASS_NAME, "swatches")
    if swatches:
        result = {}
        buttons = swatches.find_elements(By.CLASS_NAME, "buttons")
        for button in buttons:
            button.click()
            result[button.get_property("value")] = float(
                browser.driver.find_element(By.CLASS_NAME, "price")
                .text.replace("$", "")
            )
    if product.find_element(By.CLASS_NAME, "memory").text == "HDD:" and result:
        return {"hdd prices": result}
    return result


def get_single_item(browser: Browser, product: WebElement) -> Product:
    return Product(
        title=product.find_element(By.CLASS_NAME, "title")["title"],
        description=product.find_element(By.CLASS_NAME, "description").text,
        price=float(product.find_element(By.CLASS_NAME, "price")
                    .text.replace("$", "")),
        rating=int(product.find_element(By.CSS_SELECTOR,
                                        "p[data-rating]")["data-rating"]),
        num_of_reviews=product.find_element(By.CLASS_NAME,
                                            "review-count").text.split()[0],
        additional_info=parse_buttons(browser, product)
    )


def get_products_list(browser: Browser,
                      products: WebElement) -> list[Product]:
    return [get_single_item(browser, product) for product in products]


def get_items(browser: Browser, naming: str, page_link: str) -> None:
    browser.open_page(page_link)
    more_button = browser.driver.find_element(
        By.CLASS_NAME, "ecomerce-items-scroll-more"
    )
    while more_button:
        more_button.click()
        more_button = browser.driver.find_element(
            By.CLASS_NAME, "ecomerce-items-scroll-more"
        )
    products = browser.driver.find_elements(By.CLASS_NAME, "card-body")
    scrapped = get_products_list(browser, products)
    with open(f"{naming}.csv", "w") as f:
        writer = csv.writer(f)
        writer.writerow([field.name for field in fields(Product)])
        writer.writerows([(product.title,
                          product.description,
                          product.price,
                          product.rating,
                          product.num_of_reviews,
                          product.additional_info)
                          for product in scrapped])


def get_all_products() -> None:
    browser = Browser()
    for key, value in PARSE_DATA.items():
        get_items(browser, key, value)
    browser.close()


if __name__ == "__main__":
    get_all_products()
