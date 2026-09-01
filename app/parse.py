import csv
from dataclasses import dataclass, fields, astuple
from urllib.parse import urljoin

from bs4 import BeautifulSoup, Tag

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.common.exceptions import TimeoutException

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")

COMPUTERS_URL = urljoin(HOME_URL, "computers/")
LAPTOPS_URL = urljoin(COMPUTERS_URL, "laptops")
TABLETS_URL = urljoin(COMPUTERS_URL, "tablets")

PHONES_URL = urljoin(HOME_URL, "phones/")
TOUCH_URL = urljoin(PHONES_URL, "touch")

_driver: WebDriver | None = None


def get_driver() -> WebDriver:
    return _driver


def set_driver(new_driver: WebDriver) -> None:
    global _driver
    _driver = new_driver


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


PRODUCT_FIELDS = [field.name for field in fields(Product)]


def decline_cookies(driver: WebDriver) -> None:
    driver.get(HOME_URL)

    cookie_decline = WebDriverWait(driver, 10).until(
        ec.element_to_be_clickable(
            (By.CSS_SELECTOR, '[data-tid="banner-decline"]')
        )
    )
    cookie_decline.click()


def parse_single_product(product: Tag) -> Product:
    rating_element = product.select_one("p[data-rating]")

    if rating_element is not None:
        rating = int(rating_element["data-rating"])
    else:
        rating = len(product.select(".ratings .ws-icon-star"))

    return Product(
        title=product.select_one(".title")["title"],
        description=" ".join(
            product.select_one(".description").get_text().split()
        ),
        price=float(product.select_one(".price").text.replace("$", "")),
        rating=rating,
        num_of_reviews=int(
            product.select_one(".review-count").text.split()[0]
        ),
    )


def get_single_page_products(page_soup: Tag) -> list[Product]:
    products = page_soup.select(".card")
    return [parse_single_product(product) for product in products]


def get_products(url: str) -> list[Product]:
    driver = get_driver()
    driver.get(url)

    wait = WebDriverWait(driver, 2)
    wait.until(ec.presence_of_element_located((By.CSS_SELECTOR, ".card")))

    while True:
        try:
            more_button = WebDriverWait(driver, 2).until(
                ec.element_to_be_clickable(
                    (By.CSS_SELECTOR, ".ecomerce-items-scroll-more")
                )
            )
        except TimeoutException:
            break

        previous_count = len(driver.find_elements(By.CSS_SELECTOR, ".card"))

        driver.execute_script(
            "arguments[0].scrollIntoView({block: 'center'});",
            more_button,
        )
        more_button.click()

        wait.until(
            lambda current_driver: len(
                current_driver.find_elements(By.CSS_SELECTOR, ".card")
            )
            > previous_count
        )

    soup = BeautifulSoup(driver.page_source, "html.parser")
    return get_single_page_products(soup)


def write_products_to_csv(
    products: list[Product],
    output_csv_path: str
) -> None:
    with open(output_csv_path, "w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(PRODUCT_FIELDS)
        writer.writerows([astuple(product) for product in products])


def get_all_products() -> None:
    pages = {
        "home": HOME_URL,
        "computers": COMPUTERS_URL,
        "laptops": LAPTOPS_URL,
        "tablets": TABLETS_URL,
        "phones": PHONES_URL,
        "touch": TOUCH_URL,
    }

    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")

    with webdriver.Chrome(options=options) as driver:
        set_driver(driver)

        decline_cookies(driver)

        for page_name, page_url in pages.items():
            products = get_products(page_url)
            write_products_to_csv(
                products,
                f"{page_name}.csv",
            )


if __name__ == "__main__":
    get_all_products()
