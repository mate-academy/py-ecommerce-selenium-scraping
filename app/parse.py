import time
from dataclasses import dataclass, fields, astuple
from urllib.parse import urljoin
import csv
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common import NoSuchElementException
from selenium.webdriver.common.by import By


BASE_URL = "https://webscraper.io/"
ALL_URLS = {
    "HOME": urljoin(
        BASE_URL, "test-sites/e-commerce/more/"
    ),
    "COMPUTERS": urljoin(
        BASE_URL, "test-sites/e-commerce/more/computers"
    ),
    "LAPTOPS": urljoin(
        BASE_URL, "test-sites/e-commerce/more/computers/laptops"
    ),
    "TABLETS": urljoin(
        BASE_URL, "test-sites/e-commerce/more/computers/tablets"
    ),
    "PHONES": urljoin(
        BASE_URL, "test-sites/e-commerce/more/phones"
    ),
    "TOUCHES": urljoin(
        BASE_URL, "test-sites/e-commerce/more/phones/touch"
    ),
}

ALL_PATH = {
    "HOME": "home.csv",
    "COMPUTERS": "computers.csv",
    "LAPTOPS": "laptops.csv",
    "TABLETS": "tablets.csv",
    "PHONES": "phones.csv",
    "TOUCHES": "touch.csv",
}


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int
    additional_info: dict  # :TODO test does not cover it


PRODUCT_FIELDS = [field.name for field in fields(Product)]


class Parser:
    def __init__(self) -> None:
        self.driver = self.init_driver()

    @staticmethod
    def init_driver() -> webdriver:
        return webdriver.Chrome()

    def parse_hdd_block_prices(
        self,
        product_soup: BeautifulSoup
    ) -> dict[str, float] | str:
        """Functionality works, but the test doesn't cover it"""
        detailed_url = urljoin(
            BASE_URL, product_soup.select_one(".title")["href"]
        )
        self.driver.get(detailed_url)
        try:
            swatches = self.driver.find_element(By.CLASS_NAME, "swatches")
        except NoSuchElementException:
            return "No other HDD"

        buttons = swatches.find_elements(By.TAG_NAME, "button")

        prices = {}
        for button in buttons:
            if not button.get_property("disabled"):
                button.click()
                prices[button.get_property("value")] = float(self.driver.find_element(
                    By.CLASS_NAME, "price"
                ).text.replace("$", ""))

        return prices

    @staticmethod
    def parse_rating(product_soup: BeautifulSoup) -> int:
        rating_element = product_soup.select_one("p[data-rating]")
        if rating_element is not None:
            return int(rating_element.get("data-rating"))

        rating_element = product_soup.select_one(".ratings")
        star_icons = rating_element.select(".ws-icon.ws-icon-star")
        return len(star_icons)

    def parse_single_product(self, product_soup: BeautifulSoup) -> Product:
        hdd_prices = self.parse_hdd_block_prices(
            product_soup
        )  # :TODO test does not cover it
        return Product(
            title=product_soup.select_one(".title")["title"],
            description=product_soup.select_one(
                ".description"
            ).text.replace("\xa0", " "),
            price=float(product_soup.select_one(".price").text.replace("$", "")),
            rating=self.parse_rating(product_soup),
            num_of_reviews=int(
                product_soup.select_one(".ratings > p.pull-right").text.split()[0]
            ),
            additional_info={
                "hdd_prices": hdd_prices
            },  # :TODO test does not cover it
        )

    def get_single_page_products(self, page_soup: BeautifulSoup) -> [Product]:
        products = page_soup.select(".thumbnail")

        return [self.parse_single_product(product_soup) for product_soup in products]

    def check_button_more(self, url: str) -> str:
        self.driver.get(url)

        cookie_banner = self.driver.find_element(By.ID, "cookieBanner")
        if cookie_banner.is_displayed():
            cookie_banner.find_element(By.ID, "closeCookieBanner").click()

        more_button = self.driver.find_elements(
            By.CLASS_NAME, "ecomerce-items-scroll-more"
        )

        if more_button:
            while more_button[0].is_displayed():
                more_button[0].click()
                time.sleep(0.2)

        dynamic_page_source = self.driver.page_source
        return dynamic_page_source

    def get_products(self, url: str) -> list[Product]:
        page = self.check_button_more(url)

        page_soup = BeautifulSoup(page, "html.parser")
        all_products = self.get_single_page_products(page_soup)

        return all_products

    @staticmethod
    def write_products_to_csv(products: list[Product], path: str) -> None:
        with open(path, "w") as file:
            writer = csv.writer(file)
            writer.writerow(PRODUCT_FIELDS)
            writer.writerows([astuple(product) for product in products])


def get_all_products() -> None:
    parser = Parser()
    for url_key in ALL_URLS:
        print(url_key)
        products = parser.get_products(ALL_URLS[url_key])
        parser.write_products_to_csv(products, ALL_PATH[url_key])


if __name__ == "__main__":
    get_all_products()
