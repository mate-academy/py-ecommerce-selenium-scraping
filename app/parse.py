import csv
from dataclasses import dataclass, fields, astuple
from urllib.parse import urljoin

from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement

from tqdm import tqdm

from app.drive import ChromeWebDriver

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

CATEGORY_URLS = {
    "home": HOME_URL,
    "computers": urljoin(HOME_URL, "computers"),
    "laptops": urljoin(HOME_URL, "computers/laptops"),
    "tablets": urljoin(HOME_URL, "computers/tablets"),
    "touch": urljoin(HOME_URL, "phones/touch"),
    "phones": urljoin(HOME_URL, "phones"),
}


def parse_product(product_element: WebElement) -> Product:
    title = product_element.find_element(
        By.CLASS_NAME,
        "title"
    ).get_attribute("title")
    price = float(
        product_element.find_element(
            By.CLASS_NAME,
            "pull-right"
        ).text.replace("$", "")
    )
    description = product_element.find_element(
        By.CLASS_NAME,
        "description"
    ).text
    num_of_reviews = int(
        product_element.find_element(
            By.CLASS_NAME,
            "review-count"
        ).text.split()[0]
    )
    rating = len(
        product_element.find_elements(
            By.CSS_SELECTOR,
            ".ratings>p>span"
        )
    )

    return Product(
        title=title,
        description=description,
        price=price,
        rating=rating,
        num_of_reviews=num_of_reviews,
    )


def write_products_to_csv(file_name: str, products: list[Product]) -> None:
    with open(file_name, "w", newline="") as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow(PRODUCT_FIELDS)
        csvwriter.writerows([astuple(product) for product in products])


def accept_cookies(driver: WebDriver) -> None:
    button = driver.find_element(By.CLASS_NAME, "acceptCookies")
    if button:
        ActionChains(driver).click(button).perform()


def get_page_all_products(driver: WebDriver) -> None:
    while True:
        buttons = driver.find_elements(
            By.CLASS_NAME,
            "ecomerce-items-scroll-more"
        )
        if not buttons or not buttons[0].is_displayed():
            break
        ActionChains(driver).click(buttons[0]).perform()


def scrape_all_category(name: str, url: str) -> None:
    with ChromeWebDriver() as driver:
        driver.get(url)
        accept_cookies(driver)
        get_page_all_products(driver)
        product_elements = driver.find_elements(By.CLASS_NAME, "thumbnail")
        products = [
            parse_product(product)
            for product in tqdm(product_elements, desc=f"Scraping {name}")
        ]
        write_products_to_csv(f"{name}.csv", products)


def get_all_products() -> None:
    for name, url in CATEGORY_URLS.items():
        scrape_all_category(name, url)


if __name__ == "__main__":
    get_all_products()
