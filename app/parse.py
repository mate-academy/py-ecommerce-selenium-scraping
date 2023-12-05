import csv

from dataclasses import dataclass, fields
from urllib.parse import urljoin
from bs4 import BeautifulSoup, Tag
from selenium import webdriver
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions
from tqdm import tqdm


BASE_URL = "https://webscraper.io/"
PAGES = {
    "home": "test-sites/e-commerce/more/",
    "computers": "test-sites/e-commerce/more/computers",
    "phones": "test-sites/e-commerce/more/phones",
    "laptops": "test-sites/e-commerce/more/computers/laptops",
    "tablets": "test-sites/e-commerce/more/computers/tablets",
    "touch": "test-sites/e-commerce/more/phones/touch",
}


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


PRODUCT_FIELDS = [field.name for field in fields(Product)]


class DeviceParser:
    def __init__(self):
        self.driver = self.get_headless_driver()

    def get_headless_driver(self) -> WebDriver:
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        driver = webdriver.Chrome(options=chrome_options)

        return driver

    def cookies_button(self) -> None:
        try:
            accept_cookies = self.driver.find_element(
                By.CLASS_NAME, "acceptCookies"
            )
            accept_cookies.click()
        except Exception:
            pass

    def more_button_scroll(self) -> None:
        while True:
            try:
                more_button = WebDriverWait(self.driver, 5).until(
                    expected_conditions.element_to_be_clickable(
                        (By.CSS_SELECTOR, ".btn.ecomerce-items-scroll-more")
                    )
                )
                more_button.click()
            except Exception:
                break

    def parse_single_product(self, product_soup: Tag) -> Product:
        return Product(
            title=product_soup.select_one(".title")["title"],
            description=(product_soup.select_one(".description")
                         .text.replace("\xa0", " ")),
            price=float(product_soup.select_one(".price")
                        .text.replace("$", "")),
            rating=len(product_soup.select(".ws-icon")),
            num_of_reviews=int(product_soup.select_one(".review-count")
                               .text.split()[0]),
        )

    def write_products_info(
            self,
            products_list: list[Product],
            output_csv_path: str
    ) -> None:
        with open(
                output_csv_path,
                "w",
                encoding="utf-8",
                newline=""
        ) as product_file:
            writer = csv.writer(product_file)
            writer.writerow(PRODUCT_FIELDS)
            for product in products_list:
                writer.writerow(
                    [
                        product.title,
                        product.description,
                        product.price,
                        product.rating,
                        product.num_of_reviews,
                    ]
                )

    def get_all_products(self) -> None:
        for name, link in tqdm(
                PAGES.items(),
                desc="Processing download",
                unit="page"
        ):
            page = urljoin(BASE_URL, link)
            self.driver.get(page)
            self.cookies_button()
            self.more_button_scroll()
            html_page = self.driver.page_source
            page_soup = BeautifulSoup(html_page, "html.parser")
            products_soup = page_soup.select(".card-body")
            products = [
                self.parse_single_product(product) for product in products_soup
            ]
            self.write_products_info(products, f"{name}.csv")

        self.driver.quit()


if __name__ == "__main__":
    DeviceParser().get_all_products()
