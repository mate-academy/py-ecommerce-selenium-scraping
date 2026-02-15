import csv
from dataclasses import dataclass
from urllib.parse import urljoin

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions


BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


def _create_driver() -> webdriver.Chrome:
    """Create Chrome driver in headless mode."""
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--window-size=1920,1080")

    return webdriver.Chrome(options=options)


def _accept_cookies(driver: webdriver.Chrome) -> None:
    """Click accept cookies button if it appears."""
    try:
        wait = WebDriverWait(driver, 3)
        accept_button = wait.until(

            expected_conditions.element_to_be_clickable(
                (By.ID, "cookieBannerBtn")
            )
        )
        accept_button.click()
    except Exception:
        pass


def _parse_products_from_page(driver: webdriver.Chrome) -> list[Product]:
    """Parse all products currently loaded on the page."""
    products = []

    product_cards = driver.find_elements(By.CLASS_NAME, "thumbnail")

    for card in product_cards:
        title = card.find_element(
            By.CLASS_NAME, "title"
        ).get_attribute("title").strip()
        description = card.find_element(
            By.CLASS_NAME, "description"
        ).text.strip()

        price_text = card.find_element(By.CLASS_NAME, "price").text.strip()
        price = float(price_text.replace("$", ""))

        rating_elements = card.find_elements(By.CLASS_NAME, "ws-icon-star")
        rating = len(rating_elements)

        num_of_reviews = int(card.find_element(
            By.CSS_SELECTOR, "span[itemprop='reviewCount']"
        ).text.strip())

        products.append(
            Product(
                title=title,
                description=description,
                price=price,
                rating=rating,
                num_of_reviews=num_of_reviews,
            )
        )

    return products


def _load_all_products(driver: webdriver.Chrome) -> list[Product]:
    """
    Click 'More' button until it disappears
    and return all loaded products.
    """
    wait = WebDriverWait(driver, 5)

    while True:
        try:
            more_button = wait.until(
                expected_conditions.element_to_be_clickable(
                    (By.CLASS_NAME, "btn-primary")
                )
            )
            driver.execute_script("arguments[0].click();", more_button)
        except Exception:
            break

    return _parse_products_from_page(driver)


def _save_products_to_csv(file_name: str, products: list[Product]) -> None:
    """Save products list to csv file as strings for testing consistency."""
    with open(file_name, "w", newline="", encoding="utf-8") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(
            ["title", "description", "price", "rating", "num_of_reviews"]
        )

        for product in products:
            writer.writerow(
                [
                    product.title,
                    product.description,
                    str(product.price),
                    str(product.rating),
                    str(product.num_of_reviews),
                ]
            )


def _scrape_page(
        driver: webdriver.Chrome,
        page_url: str,
        file_name: str
) -> None:
    """General scraping logic for any page."""
    driver.get(page_url)
    _accept_cookies(driver)

    products = _load_all_products(driver)
    _save_products_to_csv(file_name, products)


def get_all_products() -> None:
    """Scrape all required pages and save to corresponding csv files."""
    driver = _create_driver()

    try:
        pages = {
            "home.csv": HOME_URL,
            "computers.csv": urljoin(HOME_URL, "computers"),
            "laptops.csv": urljoin(HOME_URL, "computers/laptops"),
            "tablets.csv": urljoin(HOME_URL, "computers/tablets"),
            "phones.csv": urljoin(HOME_URL, "phones"),
            "touch.csv": urljoin(HOME_URL, "phones/touch"),
        }

        for file_name, page_url in pages.items():
            _scrape_page(driver, page_url, file_name)
    finally:
        driver.quit()


if __name__ == "__main__":
    get_all_products()
