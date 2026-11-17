import csv
from dataclasses import astuple, dataclass, fields
from urllib.parse import urljoin

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait
from tqdm import tqdm


BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")

PAGES = {
    "home": HOME_URL,
    "computers": urljoin(HOME_URL, "computers"),
    "laptops": urljoin(HOME_URL, "computers/laptops"),
    "tablets": urljoin(HOME_URL, "computers/tablets"),
    "phones": urljoin(HOME_URL, "phones"),
    "touch": urljoin(HOME_URL, "phones/touch"),
}

PRODUCT_SELECTOR = ".thumbnail"
MORE_BUTTON_SELECTOR = ".ecomerce-items-scroll-more"
COOKIE_DECLINE_SELECTOR = "[data-tid='banner-decline']"

WAIT_TIMEOUT = 10
COOKIE_BANNER_TIMEOUT = 5


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


PRODUCT_FIELDS = [field.name for field in fields(Product)]


def get_text(element: WebElement, selector: str) -> str:
    return element.find_element(By.CSS_SELECTOR, selector).text


def parse_single_product(card: WebElement) -> Product:
    return Product(
        title=card.find_element(
            By.CSS_SELECTOR, ".title"
        ).get_attribute("title"),
        description=get_text(card, ".description"),
        price=float(get_text(card, ".price").replace("$", "")),
        rating=len(card.find_elements(By.CSS_SELECTOR, ".ws-icon-star")),
        num_of_reviews=int(get_text(card, ".review-count").split()[0]),
    )


def close_cookie_banner(driver: WebDriver) -> None:
    """Close the cookie banner so that it doesn't cover the "More" button."""
    try:
        WebDriverWait(driver, COOKIE_BANNER_TIMEOUT).until(
            ec.element_to_be_clickable(
                (By.CSS_SELECTOR, COOKIE_DECLINE_SELECTOR)
            )
        ).click()
    except TimeoutException:
        pass  # the banner didn't appear, nothing to close


def count_products(driver: WebDriver) -> int:
    return len(driver.find_elements(By.CSS_SELECTOR, PRODUCT_SELECTOR))


def load_all_products(driver: WebDriver) -> None:
    """Click the "More" button until it disappears.

    The click is done with JavaScript: the cookie banner can show up again
    on a new page and cover the button, which breaks a regular click.
    """
    wait = WebDriverWait(driver, WAIT_TIMEOUT)

    while True:
        more_buttons = driver.find_elements(
            By.CSS_SELECTOR, MORE_BUTTON_SELECTOR
        )
        if not more_buttons or not more_buttons[0].is_displayed():
            return

        loaded_count = count_products(driver)
        driver.execute_script("arguments[0].click();", more_buttons[0])
        wait.until(lambda browser: count_products(browser) > loaded_count)


def scrape_page(driver: WebDriver, url: str) -> list[Product]:
    driver.get(url)
    WebDriverWait(driver, WAIT_TIMEOUT).until(
        ec.presence_of_element_located((By.CSS_SELECTOR, PRODUCT_SELECTOR))
    )
    load_all_products(driver)

    return [
        parse_single_product(card)
        for card in driver.find_elements(By.CSS_SELECTOR, PRODUCT_SELECTOR)
    ]


def write_products_to_csv(products: list[Product], csv_path: str) -> None:
    with open(csv_path, "w", encoding="utf-8", newline="") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(PRODUCT_FIELDS)
        writer.writerows(astuple(product) for product in products)


def create_driver() -> WebDriver:
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--window-size=1920,1080")
    return webdriver.Chrome(options=options)


def get_all_products() -> None:
    driver = create_driver()
    try:
        driver.get(HOME_URL)
        close_cookie_banner(driver)

        with tqdm(PAGES.items(), desc="Scraping pages", unit="page") as pages:
            for page_name, url in pages:
                pages.set_postfix(page=page_name)
                products = scrape_page(driver, url)
                write_products_to_csv(products, f"{page_name}.csv")
    finally:
        driver.quit()


if __name__ == "__main__":
    get_all_products()
