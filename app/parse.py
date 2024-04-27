import csv
from dataclasses import dataclass, fields
from typing import List, Dict
from urllib.parse import urljoin


from selenium.common import NoSuchElementException
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By


from .webdriver import WebDriverContextManager, ChromeDriverConfiguration

BASE_URL = "https://webscraper.io/"
URL_DICT = {"home": "test-sites/e-commerce/more/",
            "computers": "test-sites/e-commerce/more/computers",
            "laptops": "test-sites/e-commerce/more/computers/laptops",
            "tablets": "test-sites/e-commerce/more/computers/tablets",
            "phones": "test-sites/e-commerce/more/phones",
            "touch": "test-sites/e-commerce/more/phones/touch",
            }


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


PRODUCT_FIELDS = [field.name for field in fields(Product)]


def check_and_click_button(driver: WebDriver) -> bool:
    more_button_class = "ecomerce-items-scroll-more"
    try:
        button = driver.find_element(By.CLASS_NAME, more_button_class)
    except NoSuchElementException:
        return False
    while button.is_displayed():
        try:
            button.click()
            button = driver.find_element(By.CLASS_NAME, more_button_class)
        except Exception as error:
            print(f"Click error: {error}") #TODO: implement it inside the logging
            return False
    return True


def accept_cookies(driver: WebDriver) -> None:
    try:
        accept_cookies_button = driver.find_element(
        By.CLASS_NAME, "acceptCookies"
        )
        if accept_cookies_button.is_displayed():
            accept_cookies_button.click()
    except NoSuchElementException:
        pass


def parse_single_page(driver: WebDriver, url: str) -> List[Product]:
    driver.get(url)
    accept_cookies(driver)

    check_and_click_button(driver)

    products = []
    for product in driver.find_elements(By.CLASS_NAME, "thumbnail"):
        products.append(
            Product(
                title=product.find_element(
                    By.CLASS_NAME, "title"
                ).get_attribute("title"),
                description=product.find_element(
                    By.CLASS_NAME, "description"
                ).text,
                price=float(product.find_element(
                    By.CLASS_NAME, "price"
                ).text.replace("$", "")),
                rating=len(product.find_elements(
                    By.CSS_SELECTOR, "p:nth-of-type(2) > span")
                ),
                num_of_reviews=int(product.find_element(
                    By.CLASS_NAME, "review-count"
                ).text.split()[0])
            )
        )
    return products


def get_products() -> Dict[str, List[Product]]:
    data = {}
    webdriver_name = ChromeDriverConfiguration
    with WebDriverContextManager(webdriver_name, "--headless") as driver:
        for url_name, url in URL_DICT.items():
            current_url = urljoin(BASE_URL, url)
            products = parse_single_page(driver, current_url)
            data[url_name] = products
    return data


def write_to_csv(products_data: Dict[str, List[Product]]) -> None:
    for page_name, products in products_data.items():
        output_csv_path = f"{page_name}.csv"
        with open(
                output_csv_path, "w", newline="", encoding="utf-8"
        ) as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=PRODUCT_FIELDS)
            writer.writeheader()
            for product in products:
                writer.writerow(
                    {
                        "title": product.title,
                        "description": product.description,
                        "price": product.price,
                        "rating": product.rating,
                        "num_of_reviews": product.num_of_reviews,
                    }
                )


def get_all_products() -> None:
    result = get_products()
    write_to_csv(result)


if __name__ == "__main__":
    get_all_products()
