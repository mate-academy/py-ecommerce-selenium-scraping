import csv
from dataclasses import asdict, dataclass
from urllib.parse import urljoin

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait
from tqdm import tqdm


BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")
PAGES = {
    "home": "",
    "computers": "computers",
    "laptops": "computers/laptops",
    "tablets": "computers/tablets",
    "phones": "phones",
    "touch": "phones/touch",
}
PRODUCT_SELECTOR = ".card.thumbnail"
MORE_BUTTON_SELECTOR = ".ecomerce-items-scroll-more"


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


def create_driver() -> WebDriver:
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--no-sandbox")
    return webdriver.Chrome(options=options)


def accept_cookies(driver: WebDriver) -> None:
    cookie_button_selectors = (
        "#termly-code-snippet-support",
        "button[data-tid='banner-accept']",
    )

    for selector in cookie_button_selectors:
        try:
            button = driver.find_element(By.CSS_SELECTOR, selector)
        except NoSuchElementException:
            continue

        if button.is_displayed():
            driver.execute_script("arguments[0].click();", button)
            return


def load_all_products(driver: WebDriver) -> None:
    wait = WebDriverWait(driver, 10)
    wait.until(ec.presence_of_element_located((By.CSS_SELECTOR,
                                               PRODUCT_SELECTOR)))

    while True:
        try:
            more_button = driver.find_element(
                By.CSS_SELECTOR,
                MORE_BUTTON_SELECTOR,
            )
        except NoSuchElementException:
            break

        if not more_button.is_displayed():
            break

        product_count = len(
            driver.find_elements(By.CSS_SELECTOR, PRODUCT_SELECTOR)
        )
        driver.execute_script(
            "arguments[0].scrollIntoView({block: 'center'});",
            more_button,
        )
        driver.execute_script("arguments[0].click();", more_button)
        wait.until(
            lambda current_driver: len(
                current_driver.find_elements(
                    By.CSS_SELECTOR,
                    PRODUCT_SELECTOR,
                )
            ) > product_count
        )


def parse_product(product_card: WebElement) -> Product:
    title_element = product_card.find_element(By.CSS_SELECTOR, ".title")
    price = product_card.find_element(By.CSS_SELECTOR, ".price").text
    reviews = product_card.find_element(
        By.CSS_SELECTOR,
        ".review-count",
    ).text

    return Product(
        title=title_element.get_attribute("title") or title_element.text,
        description=product_card.find_element(
            By.CSS_SELECTOR,
            ".description",
        ).text,
        price=float(price.removeprefix("$")),
        rating=len(
            product_card.find_elements(
                By.CSS_SELECTOR,
                ".ratings .ws-icon-star",
            )
        ),
        num_of_reviews=int(reviews.split()[0]),
    )


def parse_page(driver: WebDriver, url: str) -> list[Product]:
    driver.get(url)
    accept_cookies(driver)
    load_all_products(driver)
    return [
        parse_product(product_card)
        for product_card in driver.find_elements(
            By.CSS_SELECTOR,
            PRODUCT_SELECTOR,
        )
    ]


def write_products(filename: str, products: list[Product]) -> None:
    with open(filename, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=Product.__dataclass_fields__,
        )
        writer.writeheader()
        writer.writerows(asdict(product) for product in products)


def get_all_products() -> None:
    driver = create_driver()

    try:
        for page_name, path in tqdm(PAGES.items(), desc="Scraping pages"):
            products = parse_page(driver, urljoin(HOME_URL, path))
            write_products(f"{page_name}.csv", products)
            tqdm.write(f"Saved {len(products)} products to {page_name}.csv")
    finally:
        driver.quit()


if __name__ == "__main__":
    get_all_products()
