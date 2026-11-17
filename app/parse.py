import csv
from dataclasses import asdict, dataclass
from pathlib import Path
from urllib.parse import urljoin

from selenium import webdriver
from selenium.common.exceptions import (
    ElementClickInterceptedException,
    TimeoutException,
)
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait
from tqdm import tqdm


BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")

OUTPUT_DIR = Path.cwd()

PRODUCT_SELECTOR = ".thumbnail"

MORE_BUTTON_XPATH = (
    "//a[contains(normalize-space(.), 'More')]"
    " | //button[contains(normalize-space(.), 'More')]"
)

PAGES = {
    "home": ("", 3),
    "computers": ("computers", 3),
    "laptops": ("computers/laptops", 117),
    "tablets": ("computers/tablets", 21),
    "phones": ("phones", 3),
    "touch": ("phones/touch", 9),
}


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


def parse_product(element: WebElement) -> Product:
    title_element = element.find_element(
        By.CSS_SELECTOR, ".title"
    )
    title = (
        title_element.get_attribute("title")
        or title_element.text
    )

    description = element.find_element(
        By.CSS_SELECTOR, ".description"
    ).text

    price_text = element.find_element(
        By.CSS_SELECTOR, ".price"
    ).text
    price = float(
        price_text.replace("$", "").replace(",", "").strip()
    )

    rating_elements = element.find_elements(
        By.CSS_SELECTOR,
        "[data-rating]"
    )

    if rating_elements:
        rating_value = rating_elements[0].get_attribute(
            "data-rating"
        )
        rating = int(rating_value) if rating_value else 0
    else:
        stars = element.find_elements(
            By.CSS_SELECTOR,
            ".ratings .ws-icon-star"
        )
        rating = len(stars)

    reviews_text = element.find_element(
        By.CSS_SELECTOR, ".review-count"
    ).text

    num_of_reviews = int(reviews_text.split()[0])

    return Product(
        title=title,
        description=description,
        price=price,
        rating=rating,
        num_of_reviews=num_of_reviews,
    )


def parse_page(driver: WebDriver) -> list[Product]:
    elements = driver.find_elements(
        By.CSS_SELECTOR, PRODUCT_SELECTOR
    )

    return [
        parse_product(element)
        for element in elements
    ]


def accept_cookies(driver: WebDriver) -> None:
    selectors = [
        "#ez-accept-all",
        "#onetrust-accept-btn-handler",
    ]

    for selector in selectors:
        buttons = driver.find_elements(
            By.CSS_SELECTOR, selector
        )

        for button in buttons:
            if button.is_displayed():
                button.click()
                return


def load_all_products(
    driver: WebDriver,
    expected_count: int,
) -> None:
    wait = WebDriverWait(driver, 15)

    wait.until(
        lambda d: len(
            d.find_elements(
                By.CSS_SELECTOR, PRODUCT_SELECTOR
            )
        ) > 0
    )

    while True:
        current_count = len(
            driver.find_elements(
                By.CSS_SELECTOR, PRODUCT_SELECTOR
            )
        )

        if current_count >= expected_count:
            break

        buttons = driver.find_elements(
            By.XPATH, MORE_BUTTON_XPATH
        )

        visible_buttons = [
            button
            for button in buttons
            if button.is_displayed() and button.is_enabled()
        ]

        if not visible_buttons:
            raise RuntimeError(
                f"More button not found. "
                f"Loaded {current_count}/{expected_count} products."
            )

        button = visible_buttons[0]

        driver.execute_script(
            "arguments[0].scrollIntoView({block: 'center'});",
            button,
        )

        try:
            button.click()
        except ElementClickInterceptedException:
            accept_cookies(driver)
            button.click()

        try:
            wait.until(
                lambda d: len(
                    d.find_elements(
                        By.CSS_SELECTOR, PRODUCT_SELECTOR
                    )
                ) > current_count
            )
        except TimeoutException as exc:
            raise RuntimeError(
                f"Products did not load after clicking More. "
                f"Loaded: {current_count}"
            ) from exc


def save_to_csv(
    products: list[Product],
    filename: str,
) -> None:
    file_path = OUTPUT_DIR / filename

    with open(
        file_path,
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

        for product in products:
            writer.writerow(asdict(product))


def get_all_products() -> None:
    options = Options()

    # Optional: run Chrome without displaying the browser.
    options.add_argument("--headless=new")

    driver = webdriver.Chrome(options=options)

    try:
        for name, (path, expected_count) in tqdm(
                PAGES.items(),
                desc="Scraping pages",
        ):
            url = urljoin(HOME_URL, path)

            driver.get(url)
            accept_cookies(driver)

            load_all_products(
                driver,
                expected_count,
            )

            products = parse_page(driver)

            if len(products) != expected_count:
                raise RuntimeError(
                    f"{name}: expected {expected_count} products, "
                    f"found {len(products)}"
                )

            save_to_csv(
                products,
                f"{name}.csv",
            )

            tqdm.write(
                f"{name}.csv saved: {len(products)} products"
            )

    finally:
        driver.quit()


if __name__ == "__main__":
    get_all_products()
