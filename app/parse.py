from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
import csv
from dataclasses import asdict, dataclass
from urllib.parse import urljoin

from selenium import webdriver
from selenium.common.exceptions import ElementClickInterceptedException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait


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

PRODUCT_SELECTOR = ".thumbnail"
MORE_BUTTON = (
    "//button[normalize-space()='More']"
    " | //a[normalize-space()='More']"
)


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


def parse_single_product(product: WebElement) -> Product:
    title_element = product.find_element(
        By.CSS_SELECTOR, ".title"
    )
    title = title_element.get_attribute("title") or title_element.text

    description = product.find_element(
        By.CSS_SELECTOR, ".description"
    ).text

    price_text = product.find_element(
        By.CSS_SELECTOR, ".price"
    ).text

    rating = len(product.find_elements(
        By.CSS_SELECTOR, ".ratings .ws-icon-star"
    ))

    reviews_text = product.find_element(
        By.CSS_SELECTOR, ".review-count"
    ).text

    return Product(
        title=title,
        description=description,
        price=float(price_text.replace("$", "").replace(",", "")),
        rating=rating,
        num_of_reviews=int(reviews_text.split()[0]),
    )


def accept_cookies(driver: WebDriver) -> None:
    buttons = driver.find_elements(
        By.XPATH,
        "//button[contains(translate("
        "normalize-space(.), "
        "'ABCDEFGHIJKLMNOPQRSTUVWXYZ', "
        "'abcdefghijklmnopqrstuvwxyz'), 'accept')]",
    )

    for button in buttons:
        if button.is_displayed():
            button.click()
            break


def load_all_products(driver: WebDriver) -> None:
    wait = WebDriverWait(driver, 15)

    while True:
        buttons = driver.find_elements(By.XPATH, MORE_BUTTON)
        buttons = [
            button for button in buttons
            if button.is_displayed() and button.is_enabled()
        ]

        if not buttons:
            break

        previous_count = len(
            driver.find_elements(By.CSS_SELECTOR, PRODUCT_SELECTOR)
        )

        button = buttons[0]
        driver.execute_script(
            "arguments[0].scrollIntoView({block: 'center'});",
            button,
        )

        try:
            button.click()
        except ElementClickInterceptedException:
            driver.execute_script("arguments[0].click();", button)

        wait.until(
            lambda browser: len(
                browser.find_elements(
                    By.CSS_SELECTOR, PRODUCT_SELECTOR
                )
            ) > previous_count
        )


def parse_page(driver: WebDriver, url: str) -> list[Product]:
    driver.get(url)
    wait = WebDriverWait(driver, 15)

    wait.until(
        lambda browser: len(
            browser.find_elements(
                By.CSS_SELECTOR, PRODUCT_SELECTOR
            )
        ) > 0
    )

    accept_cookies(driver)
    load_all_products(driver)

    elements = driver.find_elements(
        By.CSS_SELECTOR, PRODUCT_SELECTOR
    )

    return [
        parse_single_product(element)
        for element in elements
    ]


def save_products(filename: str, products: list[Product]) -> None:
    with open(
        filename,
        "w",
        newline="",
        encoding="utf-8",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "title",
                "description",
                "price",
                "rating",
                "num_of_reviews",
            ],
        )

        writer.writeheader()
        writer.writerows(
            asdict(product) for product in products
        )


def get_all_products() -> None:
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--window-size=1920,1080")

    driver = webdriver.Chrome(options=options)

    try:
        for name, path in PAGES.items():
            url = urljoin(HOME_URL, path)
            products = parse_page(driver, url)

            save_products(f"{name}.csv", products)
            print(f"{name}: {len(products)} products")

    finally:
        driver.quit()


if __name__ == "__main__":
    get_all_products()
