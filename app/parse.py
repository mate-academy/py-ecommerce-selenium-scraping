import csv
from dataclasses import dataclass, astuple, fields
from urllib.parse import urljoin

from selenium import webdriver
from selenium.common import NoSuchElementException, TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from bs4 import BeautifulSoup, Tag

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")
COMPUTERS_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/computers")
LAPTOPS_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/computers/laptops")
TABLETS_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/computers/tablets")
PHONES_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/phones")
TOUCH_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/phones/touch")

FILENAMES_URLS = {
    "home": HOME_URL,
    "computers": COMPUTERS_URL,
    "laptops": LAPTOPS_URL,
    "tablets": TABLETS_URL,
    "phones": PHONES_URL,
    "touch": TOUCH_URL
}


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


class ChromeDriver:
    def __init__(self) -> None:
        options = Options()
        options.add_argument("--headless")
        self.driver = webdriver.Chrome(options=options)

    def quit_driver(self) -> None:
        if self.driver:
            self.driver.quit()


def accept_cookies(driver: webdriver, url: str) -> None:
    driver.get(url)
    accept_cookies_button = WebDriverWait(driver, 10).until(
        ec.element_to_be_clickable((By.CLASS_NAME, "acceptContainer"))
    )
    if accept_cookies_button.is_displayed:
        driver.execute_script(
            "arguments[0].click();",
            accept_cookies_button
        )


class FileWriter:
    def __init__(self, file_extension: str) -> None:
        self.file_extension = file_extension

    def write_to_csv(self, filename: str, data: list[Product]) -> None:
        file_path = f"{filename}.{self.file_extension}"
        with open(file_path, "w", newline="", encoding="UTF8") as file:
            writer = csv.writer(file)
            writer.writerow([field.name for field in fields(Product)])
            writer.writerows([astuple(product) for product in data])


class ProductParser:
    @staticmethod
    def parse_product(product: Tag) -> Product:
        title = product.select_one(".title")["title"]
        description = product.select_one(
            "p[class*=description]"
        ).text.replace(" ", " ")
        price = float(product.select_one(
            "h4[class*=pull-right]"
        ).text.replace("$", ""))
        rating = len(product.select("span[class*=ws-icon-star]"))
        num_of_reviews = int(product.select_one(
            "p[class*=review-count]"
        ).text.split()[0])

        return Product(
            title=title,
            description=description,
            price=price,
            rating=rating,
            num_of_reviews=num_of_reviews
        )

    def get_page_products(
            self,
            url: str,
            driver: webdriver
    ) -> list[Product]:
        accept_cookies(driver=driver, url=url)
        driver.get(url)
        try:
            while True:
                more = WebDriverWait(driver, 10).until(
                    ec.element_to_be_clickable((
                        By.CLASS_NAME,
                        "ecomerce-items-scroll-more"
                    ))
                )
                if not more.is_displayed():
                    break
                driver.execute_script(
                    "arguments[0].click();",
                    more
                )
        except NoSuchElementException:
            pass
        except TimeoutException:
            pass
        page_to_parse = driver.page_source
        soup = BeautifulSoup(page_to_parse, "html.parser")
        products = soup.select(".thumbnail")

        return [self.parse_product(product) for product in products]


def get_all_products() -> None:
    parser = ProductParser()
    driver = ChromeDriver()
    writer = FileWriter("csv")
    for filename, url in FILENAMES_URLS.items():
        products = parser.get_page_products(url=url, driver=driver.driver)
        writer.write_to_csv(filename=filename, data=products)
    driver.quit_driver()


if __name__ == "__main__":
    get_all_products()
