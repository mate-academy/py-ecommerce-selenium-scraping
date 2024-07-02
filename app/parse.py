import csv
from dataclasses import dataclass, fields, astuple
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    ElementClickInterceptedException,
    ElementNotInteractableException
)
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from app.chrome_driver import ChromeDriver

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")

ENDPOINTS_TO_PARSE = {
    "home": "",
    "computers": "computers",
    "laptops": "computers/laptops",
    "tablets": "computers/tablets",
    "phones": "phones",
    "touch": "phones/touch",
}


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int

    @classmethod
    def product_fields(cls) -> list[str]:
        return [field.name for field in fields(cls)]


class Scraper:
    def __init__(self) -> None:
        self.driver = ChromeDriver()

    @staticmethod
    def parse_single_product(product_soup: BeautifulSoup) -> Product:
        return Product(
            title=product_soup.select_one(".title")["title"],
            description=product_soup.select_one(
                ".description"
            ).text.replace("\xa0", " "),
            price=float(
                product_soup.select_one(".price").text.replace("$", "")
            ),
            rating=int(len(product_soup.find(
                "div", class_="ratings"
            ).find_all("span", class_="ws-icon"))),
            num_of_reviews=int(
                product_soup.select_one(".review-count").text.split()[0]
            )
        )

    def get_page_all_products(self, page_soup: BeautifulSoup) -> [Product]:
        return [self.parse_single_product(product_soup)
                for product_soup in page_soup.select(".card-body")]

    def parse_all_products_on_page(self, url: str) -> [Product]:
        self.driver.get(url)

        try:
            accept_cookies_button = WebDriverWait(self.driver, 2).until(
                EC.element_to_be_clickable((By.CLASS_NAME, "acceptCookies"))
            )
            accept_cookies_button.click()
            print("Cookies was accepted")
        except TimeoutException:
            print("No pop-up window accepting cookies")
        except NoSuchElementException:
            print("No item accepting cookies")

        while True:
            try:
                show_more_button = WebDriverWait(self.driver, 1).until(
                    EC.element_to_be_clickable(
                        (By.CLASS_NAME, "ecomerce-items-scroll-more")
                    )
                )
                show_more_button.click()

                WebDriverWait(self.driver, 1).until(
                    EC.presence_of_all_elements_located(
                        (By.CLASS_NAME, "thumbnail")
                    )
                )
            except TimeoutException:
                print("The 'More' button was not found or is inactive")
                break
            except NoSuchElementException:
                print("No 'More' button on the page")
                break
            except ElementClickInterceptedException:
                print(
                    "Click on the 'More' button "
                    "was intercepted by another element"
                )
                break
            except ElementNotInteractableException:
                print("The 'More' element is not interactive")
                break
        return self.get_page_all_products(
            BeautifulSoup(self.driver.page_source, "html.parser")
        )

    @staticmethod
    def write_products_to_csv(file_name: str, products: [Product]) -> None:
        with open(file_name, "w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(Product.product_fields())
            writer.writerows(astuple(product) for product in products)

    def get_all_products(self) -> None:
        for name, path in ENDPOINTS_TO_PARSE.items():
            products = self.parse_all_products_on_page(urljoin(HOME_URL, path))
            self.write_products_to_csv(f"{name}.csv", products)


get_all_products = Scraper().get_all_products


if __name__ == "__main__":
    get_all_products()
