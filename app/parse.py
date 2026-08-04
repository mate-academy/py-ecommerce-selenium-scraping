import csv
import time
from dataclasses import astuple, dataclass
from urllib.parse import urljoin

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement


BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


PAGES = {
    "home": "",
    "computers": "computers",
    "laptops": "computers/laptops",
    "tablets": "computers/tablets",
    "phones": "phones",
    "touch": "phones/touch",
}

EXPECTED_COUNTS = {
    "laptops": 117,
    "tablets": 21,
    "touch": 9,
}


def create_driver() -> WebDriver:
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--window-size=1920,1080")

    return webdriver.Chrome(options=options)


def accept_cookies(driver: WebDriver) -> None:
    try:
        button = driver.find_element(
            By.XPATH,
            "//button[contains(., 'Accept')]",
        )
        button.click()
    except NoSuchElementException:
        pass


def load_more_products(
    driver: WebDriver,
    expected_count: int,
) -> None:
    while True:
        products = driver.find_elements(
            By.CSS_SELECTOR,
            ".col-md-4.col-xl-4.col-lg-4",
        )

        if len(products) >= expected_count:
            break

        try:
            button = driver.find_element(
                By.LINK_TEXT,
                "More",
            )
        except NoSuchElementException:
            break

        driver.execute_script(
            "arguments[0].scrollIntoView();",
            button,
        )

        old_count = len(products)
        button.click()

        for _ in range(20):
            time.sleep(0.1)

            new_count = len(
                driver.find_elements(
                    By.CSS_SELECTOR,
                    ".col-md-4.col-xl-4.col-lg-4",
                )
            )

            if new_count > old_count:
                break


def parse_product(element: WebElement) -> Product:
    title_element = element.find_element(
        By.CSS_SELECTOR,
        "a.title",
    )

    title = title_element.get_attribute("title")

    if not title:
        title = title_element.text.strip()

    description = element.find_element(
        By.CSS_SELECTOR,
        ".description",
    ).text.strip()

    price_text = element.find_element(
        By.CSS_SELECTOR,
        ".price",
    ).text.strip()

    price = float(
        price_text.replace("$", "").replace(",", "")
    )

    stars = element.find_elements(
        By.CSS_SELECTOR,
        ".ratings .ws-icon-star",
    )
    rating = len(stars)

    reviews_text = element.find_element(
        By.CSS_SELECTOR,
        '[itemprop="reviewCount"]',
    ).text.strip()

    num_of_reviews = int(reviews_text)

    return Product(
        title=title,
        description=description,
        price=price,
        rating=rating,
        num_of_reviews=num_of_reviews,
    )


def parse_page(
    driver: WebDriver,
    page_name: str,
) -> list[Product]:
    url = urljoin(
        HOME_URL,
        PAGES[page_name],
    )

    driver.get(url)
    time.sleep(0.5)

    accept_cookies(driver)

    if page_name in EXPECTED_COUNTS:
        load_more_products(
            driver,
            EXPECTED_COUNTS[page_name],
        )

    elements = driver.find_elements(
        By.CSS_SELECTOR,
        ".col-md-4.col-xl-4.col-lg-4",
    )

    return [
        parse_product(element)
        for element in elements
    ]


def save_to_csv(
    filename: str,
    products: list[Product],
) -> None:
    with open(
        filename,
        "w",
        newline="",
        encoding="utf-8",
    ) as file:
        writer = csv.writer(file)

        writer.writerow(
            [
                "title",
                "description",
                "price",
                "rating",
                "num_of_reviews",
            ]
        )

        for product in products:
            writer.writerow(astuple(product))


def get_all_products() -> None:
    driver = create_driver()

    try:
        for page_name in PAGES:
            products = parse_page(
                driver,
                page_name,
            )

            save_to_csv(
                f"{page_name}.csv",
                products,
            )
    finally:
        driver.quit()


if __name__ == "__main__":
    get_all_products()
