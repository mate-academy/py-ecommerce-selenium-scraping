import csv
import time
from dataclasses import dataclass, fields, asdict

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from tqdm import tqdm

BASE_URL = "https://webscraper.io/"
URLS = {
    "home": "https://webscraper.io/test-sites/e-commerce/more",
    "computers": "https://webscraper.io/test-sites/" "e-commerce/more/computers",
    "laptops": "https://webscraper.io/test-sites/" "e-commerce/more/computers/laptops",
    "tablets": "https://webscraper.io/test-sites/" "e-commerce/more/computers/tablets",
    "phones": "https://webscraper.io/test-sites/e-commerce/more/phones",
    "touch": "https://webscraper.io/test-sites/e-commerce/more/phones/touch",
}


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


PRODUCT_FIELDS = [field.name for field in fields(Product)]


class WebScraper:

    def __init__(self, url) -> None:
        self.url = url
        self.options = Options()
        self.options.add_argument("--headless")
        self.driver = webdriver.Chrome(options=self.options)
        self.click_accept_cookies()

    def click_accept_cookies(self) -> None:
        self.driver.get(self.url)
        cookies_accept_button = self.driver.find_element(By.CLASS_NAME, "acceptCookies")
        if cookies_accept_button.is_displayed():
            cookies_accept_button.click()

    def scroll_down_page_with_more_button(self) -> None:
        self.driver.get(self.url)

        while True:
            more_button = self.driver.find_element(
                By.CSS_SELECTOR, "[class*=scroll-more]"
            )
            if more_button.is_displayed():
                more_button.click()
                time.sleep(1)
            else:
                break

    def scrape_single_page(self) -> [Product]:
        result = []
        self.driver.get(self.url)
        products = self.driver.find_elements(
            By.CSS_SELECTOR, "[class*=product-wrapper]"
        )
        for product in products:
            result.append(self.extract_product_info(product))
        return result

    def extract_product_info(self, product_element) -> Product:
        return Product(
            title=self.extract_title(product_element),
            description=self.extract_description(product_element),
            price=self.extract_price(product_element),
            rating=self.extract_rating(product_element),
            num_of_reviews=self.extract_num_of_reviews(product_element),
        )

    def extract_title(self, product_element) -> str:
        return product_element.find_element(
            By.CSS_SELECTOR, "a.title"
        ).get_attribute("textContent")

    def extract_description(self, product_element) -> str:
        return product_element.find_element(
            By.CSS_SELECTOR, "[class*=description]"
        ).text

    def extract_price(self, product_element) -> float:
        return float(
            product_element.find_element(
                By.CSS_SELECTOR, "[class*=price]"
            ).text.replace("$", "")
        )

    def extract_rating(self, product_element) -> int:
        return len(
            product_element.find_elements(By.CSS_SELECTOR, "p > span.ws-icon-star")
        )

    def extract_num_of_reviews(self, product_element) -> int:
        return int(
            product_element.find_element(
                By.CSS_SELECTOR, "[class*=review-count]"
            ).text.split()[0]
        )

    @staticmethod
    def write_to_csv(products: [Product], filename: str) -> None:
        with open(filename, "w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(PRODUCT_FIELDS)
            writer.writerows([asdict(product).values() for product in products])

    def close_driver(self) -> None:
        self.driver.quit()


def get_all_products() -> None:
    for name, url in tqdm(
        URLS.items(),
        desc="Scrapping pages",
        colour="green",
    ):
        webscraper = WebScraper(url)
        webscraper.click_accept_cookies()
        webscraper.scroll_down_page_with_more_button()
        products = webscraper.scrape_single_page()
        webscraper.write_to_csv(products, f"{name.lower()}.csv")
        webscraper.driver.quit()
        webscraper.close_driver()


if __name__ == "__main__":
    get_all_products()
