import csv
import time
from dataclasses import dataclass, astuple
from urllib.parse import urljoin
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.wait import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
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


def create_driver():
    chrome_options = Options()
    chrome_options.headless = True

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=chrome_options
    )

    return driver


def check_cookies(driver: webdriver) -> None:
    cookies_button = WebDriverWait(driver, 1).until(
        ec.element_to_be_clickable((By.CSS_SELECTOR, ".acceptCookies"))
    )
    cookies_button.click()


def to_csv(csv_file: str, products: list[Product]) -> None:
    with open(f"{csv_file}.csv", "a") as fh:
        writer = csv.writer(fh, delimiter=",")
        writer.writerow(vars(products[0]))
        writer.writerows([astuple(product) for product in products])


def get_product_details(driver: webdriver.Chrome) -> Product:
    return Product(
        title=driver.find_element(
            By.CSS_SELECTOR, ".row .caption .card-title"
        ).text,
        description=driver.find_element(
            By.CSS_SELECTOR, ".description"
        ).text,
        price=float(driver.find_element(
            By.CSS_SELECTOR, ".price"
        ).text.replace("$", "")),
        rating=len(driver.find_elements(
            By.CSS_SELECTOR, ".ws-icon-star"
        )),
        num_of_reviews=int(driver.find_element(
            By.CSS_SELECTOR, ".review-count"
        ).text.split()[0])
    )


def get_products(driver) -> None:
    products = []
    name = driver.find_elements(By.CSS_SELECTOR, ".active.nav-link")
    while True:
        more_button = driver.find_elements(
            By.CSS_SELECTOR,
            ".ecomerce-items-scroll-more:not([style='display: none;'])"
        )

        if more_button:
            more_button[0].click()
            time.sleep(1)
        else:
            break
    product_elements = driver.find_elements(By.CSS_SELECTOR, ".title")
    for product_element in product_elements:
        driver.get(product_element.get_attribute("href"))
        swatch = driver.find_elements(By.CSS_SELECTOR, ".row .swatch")
        drop = driver.find_elements(By.CSS_SELECTOR, ".row .dropdown-item")

        if swatch:
            for el in swatch:
                el.click()
                products.append(get_product_details(driver))
        else:
            if drop:
                for el in drop[1:]:
                    el.click()
                    products.append(get_product_details(driver))

        driver.back()

    to_csv(name[0].text.lower() if name else "home", products)


def get_all_products() -> None:
    with create_driver() as driver:
        driver.get(HOME_URL)
        check_cookies(driver)

        links_elements = driver.find_elements(
            By.CSS_SELECTOR, ".flex-column .nav-link"
        )
        links = [element.get_attribute("href") for element in links_elements]

        for link in links:
            driver.get(link)
            get_products(driver)

            sublinks_elements = driver.find_elements(
                By.CSS_SELECTOR, ".subcategory-link"
            )

            sublinks = [
                element.get_attribute("href") for element in sublinks_elements
            ]

            for sublink in sublinks:
                driver.get(sublink)
                get_products(driver)


if __name__ == "__main__":
    get_all_products()
