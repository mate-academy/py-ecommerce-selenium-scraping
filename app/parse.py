import csv
from dataclasses import dataclass
from urllib.parse import urljoin
from concurrent.futures import ThreadPoolExecutor

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver import ActionChains
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.chrome.options import Options


BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


class ChromeDriver:
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


def extract_product(product_element: WebElement) -> Product:
    title = product_element.find_element(
        By.CLASS_NAME, "title"
    ).get_attribute("title")

    price = float(product_element.find_element(
        By.CLASS_NAME, "pull-right"
    ).text.replace("$", ""))

    description = product_element.find_element(
        By.CLASS_NAME, "description"
    ).text

    rating_element = product_element.find_element(By.CLASS_NAME, "ratings")
    views = rating_element.find_elements(By.CSS_SELECTOR, "p")
    num_of_reviews = int(views[0].text.split()[0])
    rating = len(views[-1].find_elements(By.CSS_SELECTOR, "span"))

    return Product(
        title=title,
        description=description,
        price=price,
        rating=rating,
        num_of_reviews=num_of_reviews
    )


def save_to_csv(file_name: str, products: list[Product]) -> None:
    with open(file_name, "w", newline="") as csvfile:
        fieldnames = [
            "title",
            "description",
            "price",
            "rating",
            "num_of_reviews"
        ]

        csvwriter = csv.writer(csvfile)
        csvwriter.writerow(fieldnames)

        for product in products:
            csvwriter.writerow([
                product.title,
                product.description,
                product.price,
                product.rating,
                product.num_of_reviews
            ])


def close_cookies(driver: WebDriver) -> None:
    if len(driver.find_elements(By.CLASS_NAME, "acceptCookies")) > 0:
        button = driver.find_element(By.CLASS_NAME, "acceptCookies")
        if button.is_displayed():
            ActionChains(driver).click(button).perform()


def load_all_content(driver: WebDriver) -> None:
    if len(driver.find_elements(
            By.CLASS_NAME, "ecomerce-items-scroll-more"
    )) > 0:
        button = driver.find_element(
            By.CLASS_NAME, "ecomerce-items-scroll-more"
        )
        if button.is_displayed():
            ActionChains(driver).click(button).perform()
            load_all_content(driver)


def scrape_page(name: str, url: str) -> None:
    with ChromeDriver() as driver:
        driver.get(url)

        close_cookies(driver)
        load_all_content(driver)

        products_card = driver.find_elements(By.CLASS_NAME, "thumbnail")

        products = [extract_product(product) for product in products_card]

        save_to_csv(f"{name}.csv", products)


def get_all_products() -> None:
    pages = {
        "home": "",
        "computers": "computers",
        "laptops": "computers/laptops",
        "tablets": "computers/tablets",
        "phones": "phones",
        "touch": "phones/touch",
    }

    with ThreadPoolExecutor(max_workers=len(pages)) as executor:
        futures = [
            executor.submit(scrape_page, name, f"{HOME_URL}{url}")
            for name, url in pages.items()
        ]

    for future in futures:
        future.result()


if __name__ == "__main__":
    get_all_products()
