import csv
from dataclasses import dataclass, fields, astuple
from urllib.parse import urljoin

from selenium import webdriver
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.common.exceptions import (
    ElementClickInterceptedException,
    NoSuchElementException,
    ElementNotInteractableException,
)

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


def get_products_from_home_page(url: str, driver: WebDriver) -> list[Product]:
    products = []
    driver.get(url)
    cards = driver.find_elements(
        By.CSS_SELECTOR, ".col-md-4.col-xl-4.col-lg-4"
    )
    for card in cards:
        products.append(
            Product(
                title=card.find_element(
                    By.CLASS_NAME, "title"
                ).get_attribute("title"),
                description=card.find_element(
                    By.CLASS_NAME, "description"
                ).text,
                price=float(
                    card.find_element(
                        By.CLASS_NAME, "price"
                    ).text.replace("$", "")
                ),
                rating=int(
                    card.find_element(
                        By.CSS_SELECTOR, "p[data-rating]"
                    ).get_attribute("data-rating")
                ),
                num_of_reviews=int(
                    card.find_element(
                        By.CLASS_NAME, "review-count"
                    ).text.split()[0]
                ),
            )
        )

    return products


def get_random_products(
        url: str,
        driver: WebDriver,
        selector: str
) -> list[Product]:
    products = []
    driver.get(url)
    products_link = driver.find_element(By.CSS_SELECTOR, selector)
    products_link.click()

    WebDriverWait(driver, 10).until(
        expected_conditions.presence_of_element_located((
            By.CSS_SELECTOR, ".col-md-4.col-xl-4.col-lg-4"
        ))
    )

    cards = driver.find_elements(
        By.CSS_SELECTOR, ".col-md-4.col-xl-4.col-lg-4"
    )

    for card in cards:
        products.append(
            Product(
                title=card.find_element(
                    By.CLASS_NAME, "title"
                ).get_attribute("title"),
                description=card.find_element(
                    By.CLASS_NAME,
                    "description"
                ).text,
                price=float(
                    card.find_element(
                        By.CLASS_NAME, "price"
                    ).text.replace("$", "")
                ),
                rating=int(
                    card.find_element(
                        By.CSS_SELECTOR,
                        "p[data-rating]"
                    ).get_attribute(
                        "data-rating"
                    )
                ),
                num_of_reviews=int(
                    card.find_element(
                        By.CLASS_NAME,
                        "review-count"
                    ).text.split()[0]
                ),
            )
        )

    return products


def close_cookie_banner(driver: WebDriver) -> None:
    try:
        cookie_button = WebDriverWait(driver, 10).until(
            expected_conditions.element_to_be_clickable(
                (By.CSS_SELECTOR, "#closeCookieBanner")
            )  # .acceptCookies
        )
        cookie_button.click()

    except (NoSuchElementException, ElementClickInterceptedException):
        pass


def get_all_products_from_page(
    url: str, driver: WebDriver, main_selector: str, selector: str
) -> list[Product]:
    products = []
    driver.get(url)

    products_link = driver.find_element(By.CSS_SELECTOR, main_selector)
    products_link.click()

    WebDriverWait(driver, 10).until(
        expected_conditions.presence_of_element_located((
            By.CSS_SELECTOR,
            ".nav.nav-second-level"
        ))
    )

    all_products_link = driver.find_element(By.CSS_SELECTOR, selector)
    all_products_link.click()

    WebDriverWait(driver, 10).until(
        expected_conditions.presence_of_element_located(
            (By.CSS_SELECTOR, ".row.ecomerce-items.ecomerce-items-more")
        )
    )

    count_more_btn = 1
    while True:
        try:
            more_btn = driver.find_element(
                By.CSS_SELECTOR,
                ".btn.btn-lg.btn-block.btn-primary.ecomerce-items-scroll-more",
            )
            if more_btn:
                more_btn.click()
            else:
                break

            WebDriverWait(driver, 10).until(
                expected_conditions.presence_of_element_located((
                    By.CSS_SELECTOR,
                    ".row.ecomerce-items.ecomerce-items-more"
                ))
            )
            count_more_btn += 1
        except ElementClickInterceptedException:
            close_cookie_banner(driver)
        except ElementNotInteractableException:
            break

    WebDriverWait(driver, 10).until(
        expected_conditions.presence_of_element_located((
            By.CSS_SELECTOR, ".col-md-4.col-xl-4.col-lg-4"
        ))
    )

    cards = driver.find_elements(
        By.CSS_SELECTOR, ".col-md-4.col-xl-4.col-lg-4"
    )

    for card in cards:
        products.append(
            Product(
                title=card.find_element(
                    By.CLASS_NAME,
                    "title"
                ).get_attribute("title"),
                description=card.find_element(
                    By.CLASS_NAME,
                    "description"
                ).text,
                price=float(
                    card.find_element(
                        By.CLASS_NAME,
                        "price"
                    ).text.replace("$", "")
                ),
                rating=len(
                    card.find_elements(
                        By.CSS_SELECTOR,
                        ".ratings p span.ws-icon"
                    )
                ),
                num_of_reviews=int(
                    card.find_element(
                        By.CSS_SELECTOR,
                        ".ratings > .review-count.float-end.pull-right"
                    ).text.split()[0]
                ),
            )
        )

    return products


def write_products_to_csv_file(
        products: [Product],
        output_csv_path: str
) -> None:
    with open(output_csv_path, "w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(PRODUCT_FIELDS)
        writer.writerows([astuple(quote) for quote in products])


def get_all_products() -> None:
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    with webdriver.Chrome(options=options) as driver:
        home_page_products = get_products_from_home_page(HOME_URL, driver)
        write_products_to_csv_file(home_page_products, "home.csv")

        computer_page = get_random_products(
            HOME_URL, driver, "a[href='/test-sites/e-commerce/more/computers']"
        )
        write_products_to_csv_file(computer_page, "computers.csv")

        laptop_page = get_all_products_from_page(
            HOME_URL,
            driver,
            "a[href='/test-sites/e-commerce/more/computers']",
            "a[href='/test-sites/e-commerce/more/computers/laptops']",
        )
        write_products_to_csv_file(laptop_page, "laptops.csv")

        tablets_page = get_all_products_from_page(
            HOME_URL,
            driver,
            "a[href='/test-sites/e-commerce/more/computers']",
            "a[href='/test-sites/e-commerce/more/computers/tablets']",
        )
        write_products_to_csv_file(tablets_page, "tablets.csv")

        phones_page = get_random_products(
            HOME_URL, driver, "a[href='/test-sites/e-commerce/more/phones']"
        )
        write_products_to_csv_file(phones_page, "phones.csv")

        touch_page = get_all_products_from_page(
            HOME_URL,
            driver,
            "a[href='/test-sites/e-commerce/more/phones']",
            "a[href='/test-sites/e-commerce/more/phones/touch']",
        )
        write_products_to_csv_file(touch_page, "touch.csv")


if __name__ == "__main__":
    get_all_products()
