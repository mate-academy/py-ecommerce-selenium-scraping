from dataclasses import dataclass
from urllib.parse import urljoin
import time
import csv
import os

from tqdm import tqdm
from dotenv import load_dotenv
from bs4 import BeautifulSoup, Tag
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By


load_dotenv()


BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")
COMPUTERS_URL = urljoin(HOME_URL, "computers/")
TABLETS_URL = urljoin(COMPUTERS_URL, "tablets")
LAPTOPS_URL = urljoin(COMPUTERS_URL, "laptops")
PHONES_URL = urljoin(HOME_URL, "phones/")
TOUCH_URL = urljoin(PHONES_URL, "touch")

PAGE_URLS = {
    "home": HOME_URL,
    "computers": COMPUTERS_URL,
    "tablets": TABLETS_URL,
    "laptops": LAPTOPS_URL,
    "phones": PHONES_URL,
    "touch": TOUCH_URL,
}


class WebDriverManager:
    def __init__(self, headless: bool = True):
        chromedriver_path = os.getenv("CHROMEDRIVER_PATH")
        if not chromedriver_path:
            raise ValueError(
                "CHROMEDRIVER_PATH environment variable is not set."
                )

        self.service = Service(executable_path=chromedriver_path)
        chrome_options = Options()
        if headless:
            chrome_options.add_argument("--headless")

        self.driver = webdriver.Chrome(
            service=self.service,
            options=chrome_options
            )

    def navigate_to(self, url: str):
        self.driver.get(url)

    def click_element(self, by: By, value: str, timeout: int = 3):
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.element_to_be_clickable((by, value))
            )
            element.click()
            print(f"Clicked element with locator: {by}, value: {value}")
        except NoSuchElementException:
            print(f"Element not found: {by}, value: {value}")
        except Exception as e:
            print(f"An error occurred: {e}")

    def get_page_source(self) -> str:
        return self.driver.page_source

    def close(self):
        self.driver.quit()


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


def fetch_page(url: str, driver_manager: WebDriverManager) -> BeautifulSoup:
    driver_manager.navigate_to(url)
    cookie_accept(url, driver_manager)

    more_button = driver_manager.driver.find_elements(
        By.CLASS_NAME,
        "ecomerce-items-scroll-more"
    )
    max_retries = 100
    with tqdm(
        total=max_retries,
        desc="Loading more items",
        unit="click", ncols=100
    ) as pbar:
        while more_button and pbar.n < max_retries:
            if more_button[0].value_of_css_property("display") == "none":
                print("No more 'More' button (display: none).")
                break

            try:
                driver_manager.click_element(
                    By.CLASS_NAME,
                    "ecomerce-items-scroll-more"
                )
                print("Clicked 'More' button.")
                time.sleep(1)
                pbar.update(1)
                more_button = driver_manager.driver.find_elements(
                    By.CLASS_NAME,
                    "ecomerce-items-scroll-more"
                    )
            except NoSuchElementException:
                print("No more 'More' button.")
                break
            except Exception as e:
                print(f"An error occurred: {e}")
                break
    
    page_source = driver_manager.get_page_source()
    return BeautifulSoup(page_source, "html.parser")


def cookie_accept(url: str, driver_manager: WebDriverManager) -> None:
    driver_manager.navigate_to(url)
    driver_manager.click_element(
        By.XPATH,
        '//*[@id="cookieBanner"]/div[2]/button'
    )


def parse_single_product(soup: Tag) -> Product:
    title = soup.find(class_="title").text.strip()
    description = soup.find(class_="description").text.strip()
    price = float(soup.find(class_="price").text.strip().replace("$", ""))
    rating = len(soup.find_all("span", class_="ws-icon ws-icon-star"))
    num_of_reviews = int(soup.find(class_="review-count").text.split()[0])
    return Product(
        title=title,
        description=description,
        price=price,
        rating=rating,
        num_of_reviews=num_of_reviews
    )


def extract_all_products(soup: Tag) -> list[Product]:
    all_products = soup.find_all('div', class_='col-md-4 col-xl-4 col-lg-4')
    print(f"Found {len(all_products)} products")
    products_list = []
    for product in tqdm(
        all_products,
        desc="Extracting all products...",
        ncols=100
        ):
        products_list.append(parse_single_product(product))
    return products_list


def write_to_csv(file_name: str, products: list[Product]) -> None:
    with open(file_name, mode="w", newline="", encoding="utf-8") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow([
            "Title",
            "Dscription",
            "Price",
            "Rating",
            "Number of Reviews"
        ]
        )
        for product in tqdm(
            products,
            desc="Writing to csv files...",
            ncols=100
        ):
            writer.writerow(
                [
                    product.title,
                    product.description,
                    product.price,
                    product.rating,
                    product.num_of_reviews
                ]
            )
        print(f"Data written to {file_name}")


def get_all_products() -> None:
    driver_manager = WebDriverManager()
    try:
        for page_name, url in PAGE_URLS.items():
            print(f"Processing page: {page_name}")
            soup = fetch_page(url, driver_manager)
            products = extract_all_products(soup)
            file_name = f"{page_name}.csv"
            write_to_csv(file_name, products)
    finally:
        driver_manager.close()


if __name__ == "__main__":
    get_all_products()
