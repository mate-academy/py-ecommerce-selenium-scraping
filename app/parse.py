import csv
from selenium.webdriver import Chrome
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from dataclasses import dataclass
from urllib.parse import urljoin
from bs4 import BeautifulSoup, ResultSet, Tag

BASE_URL = "https://webscraper.io/"
PAGES_URLS = {
    "home": "test-sites/e-commerce/more",
    "computers": "test-sites/e-commerce/more/computers",
    "laptops": "test-sites/e-commerce/more/computers/laptops",
    "tablets": "test-sites/e-commerce/more/computers/tablets",
    "phones": "test-sites/e-commerce/more/phones",
    "touch": "test-sites/e-commerce/more/phones/touch",
}


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


class ScrapTestSite:
    """Class to scrap test site"""
    def __init__(self) -> None:
        print("Open browser")
        opts = Options()
        opts.headless = True
        self.driver = Chrome(options=opts)

    def close_browser(self) -> None:
        print("Close browser")
        self.driver.close()

    def open_page(self, page_url: str) -> None:
        self.driver.get(page_url)

    def click_more_button(self) -> None:
        while True:
            try:
                more_button = WebDriverWait(self.driver, 1).until(
                    ec.element_to_be_clickable(
                        (By.CSS_SELECTOR, ".btn.btn-lg.btn-block"
                                          ".btn-primary"
                                          ".ecomerce-items-scroll-more")
                    )
                )
                print("Click button...")
                more_button.click()
            except Exception:
                print("No more buttons available")
                break

    def check_cookies(self) -> None:
        try:
            accept_cookies = WebDriverWait(self.driver, 2).until(
                ec.element_to_be_clickable((By.CLASS_NAME, "acceptCookies"))
            )
            print("Accept cookies")
            accept_cookies.click()
        except Exception:
            print("No cookies to accept!")

    @staticmethod
    def get_pages() -> dict[str, str]:
        return {
            page_name: urljoin(BASE_URL, page_url)
            for page_name, page_url in PAGES_URLS.items()
        }

    def scrap_pages(self) -> None:
        pages = self.get_pages()

        for page_name, page_url in pages.items():
            print(f"Processing page: {page_name}")
            self.open_page(page_url)
            self.check_cookies()
            self.click_more_button()
            page_source = self.driver.page_source
            parser = PageParser(page_source)
            print("Collecting data...")
            products = parser.get_products_content()
            print(f"Write data to {page_name}.csv")
            CSVWriter.write_to_csv(products, f"{page_name}.csv")

        self.close_browser()


class PageParser:
    """Class to parse page content and extract product information"""
    def __init__(self, page: str) -> None:
        self.page_source = page

    def get_page_soup(self) -> BeautifulSoup:
        return BeautifulSoup(self.page_source, "html.parser")

    def get_card_body_info(self) -> ResultSet[Tag]:
        return self.get_page_soup().find_all("div", class_="card-body")

    def get_products_content(self) -> list[Product]:
        products_soup = self.get_card_body_info()
        products_list = []

        for product in products_soup:
            products_list.append(Product(
                title=product.select_one(".title")["title"],
                description=(
                    product.select_one(".description")
                    .get_text().replace("\xa0", " ")
                ),
                price=float(
                    product.select_one(".price").get_text().replace("$", "")
                ),
                rating=len(product.select(".ws-icon")),
                num_of_reviews=int(
                    product.select_one(".review-count").get_text().split()[0]
                ),
            ))

        return products_list


class CSVWriter:
    """Class to write product data to a CSV file"""
    @staticmethod
    def write_to_csv(products: list[Product], file_name: str) -> None:
        fieldnames = [
            "title",
            "description",
            "price",
            "rating",
            "num_of_reviews",
        ]
        with open(file_name, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for product in products:
                row = {
                    "title": product.title,
                    "description": product.description,
                    "price": product.price,
                    "rating": product.rating,
                    "num_of_reviews": product.num_of_reviews,
                }
                writer.writerow(row)


def get_all_products() -> None:
    """Save all pages to corresponding .csv files"""
    site_to_scrap = ScrapTestSite()
    site_to_scrap.scrap_pages()


if __name__ == "__main__":
    get_all_products()
