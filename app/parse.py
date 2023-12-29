import csv
from dataclasses import dataclass, astuple, fields
from urllib.parse import urljoin

from bs4 import Tag, BeautifulSoup

from selenium.common import NoSuchElementException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver import Chrome
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement


BASE_URL = "https://webscraper.io/"

HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")
COMPUTERS_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/computers")
LAPTOPS_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/computers/laptops")
TABLETS_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/computers/tablets")
PHONES_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/phones")
TOUCH_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/phones/touch")

LINKS_TO_PARSE = {
    "home.csv": HOME_URL,
    "computers.csv": COMPUTERS_URL,
    "laptops.csv": LAPTOPS_URL,
    "tablets.csv": TABLETS_URL,
    "phones.csv": PHONES_URL,
    "touch.csv": TOUCH_URL
}


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


class ProductParser:
    def __init__(self) -> None:
        options = Options()
        options.add_argument("--headless")
        self.driver = Chrome(options=options)

    def quit_driver(self) -> None:
        if self.driver:
            self.driver.quit()

    def handle_find_element(self, by: str, value: str) -> None | WebElement:
        try:
            element = self.driver.find_element(by, value)
            return element
        except NoSuchElementException:
            return None

    def accept_cookies(self) -> None:
        accept_button = self.handle_find_element(
            By.CSS_SELECTOR, "a.acceptCookies"
        )
        if accept_button:
            accept_button.click()

    @staticmethod
    def parse_single_product(product_soup: Tag) -> Product:
        return Product(
            title=product_soup.select_one("a.title")["title"],
            description=product_soup.select_one(
                "p.description"
            ).text.replace("\xa0", " "),
            price=float(
                product_soup.select_one("h4.price").text.replace("$", "")
            ),
            rating=len(product_soup.select(".ws-icon-star")),
            num_of_reviews=int(
                product_soup.select_one("p.review-count").text.split()[0]
            )
        )

    def parse_page(self, url: str) -> list[Product]:
        self.driver.get(url)
        self.accept_cookies()
        more_button = self.handle_find_element(
            By.CSS_SELECTOR,
            'a.ecomerce-items-scroll-more:not([style*="none"])'
        )
        while more_button:
            if (
                more_button.is_enabled()
                and more_button.is_displayed()
            ):
                self.driver.execute_script(
                    "arguments[0].click();", more_button
                )
                more_button = self.handle_find_element(
                    By.CSS_SELECTOR,
                    'a.ecomerce-items-scroll-more:not([style*="none"])'
                )
            else:
                break
        products_soup = BeautifulSoup(
            self.driver.page_source, "html.parser"
        ).select(".card.product-wrapper")

        return [
            self.parse_single_product(product_soup)
            for product_soup in products_soup
        ]

    @staticmethod
    def write_to_csv(products: list[Product], filename: str) -> None:
        with open(filename, "w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow([field.name for field in fields(Product)])
            writer.writerows([astuple(product) for product in products])


def get_all_products() -> None:
    parser = ProductParser()
    try:
        for filename, url in LINKS_TO_PARSE.items():
            parser.write_to_csv(
                parser.parse_page(url),
                filename
            )
    except Exception as e:
        print(f"Error: {e}")
    finally:
        parser.quit_driver()


if __name__ == "__main__":
    get_all_products()
