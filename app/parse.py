import csv
import logging
import sys
import time
from dataclasses import astuple, dataclass, fields
from types import TracebackType
from urllib.parse import urljoin

from selenium import webdriver
from selenium.common import (
    ElementNotInteractableException,
    NoSuchElementException,
)
from selenium.webdriver import ActionChains
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from tqdm import tqdm
from webdriver_manager.chrome import ChromeDriverManager


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
PAGES_WITH_MORE_BUTTON = [PAGES["laptops"], PAGES["tablets"], PAGES["touch"]]


logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


class Scraper:
    """Class for scraping products from e-commerce website."""

    def __init__(self) -> None:
        """Initialize Chrome driver in headless mode."""
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")

        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)

    def __enter__(self) -> "Scraper":
        """Context manager enter method."""
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Context manager exit method."""
        self.driver.quit()

    def accept_cookies(self) -> None:
        """Accept cookies on the website."""
        try:
            accept_button = self.driver.find_element(
                By.CSS_SELECTOR, "button.acceptCookies"
            )
            accept_button.click()
        except (NoSuchElementException, ElementNotInteractableException):
            pass

    def click_more_button(self) -> bool:
        """Click "More" button to load additional products."""
        try:
            more_button = self.driver.find_element(
                By.CSS_SELECTOR, "a.ecomerce-items-scroll-more"
            )
            actions = ActionChains(self.driver)
            actions.move_to_element(more_button).perform()
            more_button.click()

            return True

        except ElementNotInteractableException:
            return False

    @staticmethod
    def parse_single_product(product_element: WebElement) -> Product:
        """Parse single product data from HTML element."""
        title = product_element.find_element(
            By.CSS_SELECTOR, "a.title"
        ).get_attribute("title")
        description = product_element.find_element(
            By.CSS_SELECTOR, "p.description"
        ).text
        price = float(
            product_element.find_element(
                By.CSS_SELECTOR, "h4.price"
            ).text.replace("$", "")
        )
        rating_element = product_element.find_element(
            By.CSS_SELECTOR, "div.ratings"
        )
        rating = len(
            rating_element.find_elements(By.CSS_SELECTOR, "span.ws-icon-star")
        )
        num_of_reviews = int(
            product_element.find_element(
                By.CSS_SELECTOR, "p.review-count"
            ).text.split()[0]
        )

        return Product(title, description, price, rating, num_of_reviews)

    def get_products_from_page(self, url: str) -> list[Product]:
        """Get all products from a page."""
        self.driver.get(url)
        self.accept_cookies()

        if url in PAGES_WITH_MORE_BUTTON:
            while self.click_more_button():
                continue

        product_elements = self.driver.find_elements(
            By.CLASS_NAME, "card-body"
        )

        products = []
        for element in product_elements:
            product = self.parse_single_product(element)
            products.append(product)

        return products

    @staticmethod
    def save_to_csv(products: list[Product], filename: str) -> None:
        """Save products to CSV file."""
        with open(filename, "w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow([field.name for field in fields(Product)])
            writer.writerows([astuple(product) for product in products])


def get_all_products() -> None:
    """Scrape all products from all pages and save results to CSV files."""
    with Scraper() as scraper:
        for page_name, url in tqdm(
            PAGES.items(), desc="Parsing pages", unit="page", colour="green"
        ):
            products = scraper.get_products_from_page(url)
            scraper.save_to_csv(products, f"{page_name}.csv")


if __name__ == "__main__":
    start_time = time.time()

    logging.info("Parsing started...")
    get_all_products()
    execution_time = time.time() - start_time

    logging.info(
        f"\nTotal execution time: {execution_time:.2f} seconds"  # noqa: E231
    )
    logging.info(
        "\nParsing completed successfully! "
        "CSV files with results have been created for each page:"
    )
    for page_name in PAGES.keys():
        logging.info(f"- {page_name}.csv")
