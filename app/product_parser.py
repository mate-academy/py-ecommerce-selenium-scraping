import time
from selenium import webdriver
from selenium.common import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from tqdm import tqdm
from app.models import Product
from app.utils import save_to_csv


class ProductParser:
    def __init__(self, driver: webdriver.Chrome) -> None:
        self.driver = driver
        self.cookies_accepted = False

    def parse_page(self, url: str, file_name: str) -> list[Product]:
        self.driver.get(url)
        if not self.cookies_accepted:
            self.accept_cookies()
        self.handle_pagination()
        items = self.driver.find_elements(
            By.CLASS_NAME, "product-wrapper"
        )
        products = []
        with tqdm(total=len(items),
                  desc="Parsing Products", unit_scale=True) as pbar:
            for item in items:
                product = self.scrape_product(item)
                products.append(product)
                pbar.update(1)
        save_to_csv(file_name, products)
        return products

    def scrape_product(self, item: WebElement) -> Product:
        title = item.find_element(By.CLASS_NAME,
                                  "title").get_attribute("title")
        description = item.find_element(By.CLASS_NAME, "description").text
        price = float(item.find_element(By.CLASS_NAME, "price").text[1:])
        rating = len(item.find_elements(By.CLASS_NAME, "ws-icon-star"))
        num_of_reviews = int(item.find_element(
            By.CLASS_NAME,
            "review-count"
        ).text.split()[0])
        return Product(title, description, price, rating, num_of_reviews)

    def accept_cookies(self) -> None:
        try:
            cookies_accept = self.driver.find_element(By.CLASS_NAME,
                                                      "acceptCookies")
            cookies_accept.click()
        except NoSuchElementException:
            print("Cookies were already accepted (accept button not found)")
        self.cookies_accepted = True

    def handle_pagination(self) -> None:
        while True:
            try:
                pagination_button = self.driver.find_element(
                    By.CLASS_NAME,
                    "ecomerce-items-scroll-more"
                )
                if pagination_button.is_displayed():
                    pagination_button.click()
                    time.sleep(0.1)
                else:
                    break
            except NoSuchElementException:
                break
        time.sleep(1)
