import csv
from dataclasses import dataclass, fields, astuple
from urllib.parse import urljoin

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver import ActionChains
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.by import By

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


class ChromeWebDriver:
    def __init__(self) -> None:
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        self._driver = webdriver.Chrome(options=chrome_options)

    def __enter__(self) -> WebDriver:
        return self._driver

    def __exit__(
            self,
            exc_type: type,
            exc_val: Exception,
            exc_tb: type
    ) -> None:
        self._driver.close()


def parse(product_element: WebElement) -> Product:
    title = product_element.find_element(
        By.CLASS_NAME,
        "title"
    ).get_attribute("title")
    price = product_element.find_element(
        By.CLASS_NAME,
        "pull-right"
    ).text.replace(
        "$", ""
    )
    description = product_element.find_element(
        By.CLASS_NAME,
        "description"
    ).text
    rating_element = product_element.find_element(By.CLASS_NAME, "ratings")
    views = rating_element.find_elements(By.CSS_SELECTOR, "p")
    num_of_reviews = views[0].text.split()[0]
    rating = len(views[-1].find_elements(By.CSS_SELECTOR, "span"))

    return Product(
        title=title,
        description=description,
        price=float(price),
        rating=rating,
        num_of_reviews=int(num_of_reviews),
    )


def save_products_to_csv(file_name: str, products: list[Product]) -> None:
    with open(file_name, "w", newline="") as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow(PRODUCT_FIELDS)
        csvwriter.writerows([astuple(product) for product in products])


def handle_cookies(driver: WebDriver) -> None:
    if len(driver.find_elements(By.CLASS_NAME, "acceptCookies")) > 0:
        button = driver.find_element(By.CLASS_NAME, "acceptCookies")
        if button.is_displayed():
            ActionChains(driver).click(button).perform()


def load_more_products(driver: WebDriver) -> None:
    while True:
        buttons = driver.find_elements(
            By.CLASS_NAME,
            "ecomerce-items-scroll-more"
        )
        if not buttons:
            break
        button = buttons[0]
        if button.is_displayed():
            ActionChains(driver).click(button).perform()
        else:
            break


def scrape_category(name: str, url: str) -> None:
    with ChromeWebDriver() as driver:
        driver.get(url)
        handle_cookies(driver)
        load_more_products(driver)
        product_elements = driver.find_elements(By.CLASS_NAME, "thumbnail")
        products = [parse(product) for product in product_elements]
        print(f"Scraping {name}")
        save_products_to_csv(f"{name}.csv", products)


def get_all_products() -> None:
    for name, url in CATEGORY_URLS.items():
        scrape_category(name, url)


if __name__ == "__main__":
    get_all_products()
