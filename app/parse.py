import csv
from dataclasses import dataclass
import time
from urllib.parse import urljoin

from selenium import webdriver
from selenium.common import NoSuchElementException, ElementClickInterceptedException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from tqdm import tqdm
from selenium.webdriver.chrome.webdriver import WebDriver

BASE_URL = "https://webscraper.io/"
ALL_PAGE = {
    "home": "test-sites/e-commerce/more/",
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


def set_driver() -> Options:
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--log-level=3")
    options.add_argument("--silent")
    return options


def accept_cookies(banner: WebElement) -> None:
    accept_button = banner.find_element(
        By.CSS_SELECTOR, ".acceptContainer > button.acceptCookies"
    )
    accept_button.click()


def get_products(element: WebElement, category: str) -> Product:
    return Product(
        title=element.find_element(
            By.CSS_SELECTOR, ".caption > h4 > a"
        ).get_attribute("title"),
        description=element.find_element(
            By.CSS_SELECTOR, ".caption > p.description"
        ).text,
        price=float(element.find_element(
            By.CSS_SELECTOR, ".caption > h4.float-end"
        ).text.replace("$", "")),
        rating=len(element.find_elements(
            By.CSS_SELECTOR, ".ratings span.ws-icon-star")
        ),
        num_of_reviews=int(
            element.find_element(
                By.CSS_SELECTOR, ".ratings > p.review-count"
            ).text.split(" ")[0]),
    )


def save_in_csv(products: [Product], filename: str) -> None:
    with open(f"{filename}.csv", "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["title", "description", "price", "rating", "num_of_reviews"])
        for product in products:
            writer.writerow([
                product.title,
                product.description,
                product.price,
                product.rating,
                product.num_of_reviews,
            ])


def parse_product_page(driver: WebDriver, url: str, category: str) -> [Product]:
    driver.get(urljoin(BASE_URL, url))
    products = []
    try:
        cookie_banner = driver.find_element(By.ID, "cookieBanner")
        accept_cookies(cookie_banner)
    except:
        pass

    while True:
        product_elements = driver.find_elements(By.CSS_SELECTOR, ".thumbnail")
        for element in product_elements:
            if not element.text.strip():
                continue
            products.append(get_products(element, category))

        try:
            more_button = driver.find_element(
                By.CLASS_NAME, "ecomerce-items-scroll-more"
            )
            if not more_button.is_displayed():
                break
            driver.execute_script(
                "arguments[0].scrollIntoView(true);", more_button
            )
            time.sleep(1)

            try:
                more_button.click()
                time.sleep(2)
            except ElementClickInterceptedException:
                break

        except NoSuchElementException:
            break
    return products


def get_all_products() -> None:
    driver_options = set_driver()

    tqdm_obj = tqdm(
        ALL_PAGE.items(),
        desc=f"Scraping products from {BASE_URL}",
        total=len(ALL_PAGE), leave=True
    )
    driver = webdriver.Chrome(options=driver_options)
    for filename, url in tqdm_obj:
        tqdm_obj.set_description(f"Scraping products from {BASE_URL} ({filename})")
        products = parse_product_page(driver, url, filename)
        save_in_csv(products, filename)
    driver.quit()


if __name__ == "__main__":
    get_all_products()
