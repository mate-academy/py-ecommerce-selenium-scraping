from urllib.parse import urljoin
import time
import csv
from typing import List

from selenium.common import NoSuchElementException, TimeoutException
from tqdm import tqdm
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.remote.webelement import WebElement

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")


class Product:
    def __init__(
            self,
            title: str,
            description: str,
            price: float,
            rating: int,
            num_of_reviews: int
    ):
        self.title = title
        self.description = description
        self.price = price
        self.rating = rating
        self.num_of_reviews = num_of_reviews

    def to_csv_row(self) -> List:
        return [self.title, self.description, self.price, self.rating,
                self.num_of_reviews]

    def __eq__(self, other) -> bool:
        if not isinstance(other, Product):
            return False
        return (self.title == other.title and
                self.description == other.description and
                self.price == other.price and
                self.rating == other.rating and
                self.num_of_reviews == other.num_of_reviews)


def create_driver() -> webdriver.Chrome:
    options = Options()
    options.add_argument("--headless")
    return webdriver.Chrome(options=options)


def wait_for_element(
        driver: webdriver.Chrome,
        by: str,
        value: str,
        timeout: float = 10
) -> WebElement:
    by_types = {
        "id": By.ID,
        "css_selector": By.CSS_SELECTOR,
        "tag_name": By.TAG_NAME,
        "xpath": By.XPATH,
    }
    by_type = by_types.get(by.lower(), By.ID)
    return WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((by_type, value))
    )


def click_element(driver: webdriver.Chrome, element: WebElement) -> None:
    driver.execute_script("arguments[0].scrollIntoView(true);", element)
    driver.execute_script("arguments[0].click();", element)


def close_cookie_banner(driver: webdriver.Chrome) -> None:
    try:
        wait_for_element(driver, "id", "cookieBanner", timeout=3)
        driver.execute_script(
            """
                        var banner = document.getElementById('cookieBanner');
                        if (banner) banner.style.display = 'none';
                    """
        )
        print("Cookie banner closed.")
    except TimeoutException:
        print("Cookie banner not found, proceeding.")


def click_more_until_disappear(
        driver: webdriver.Chrome,
        max_retries: int = 10
) -> None:
    close_cookie_banner(driver)
    retries = 0
    while retries < max_retries:
        try:
            more_link = WebDriverWait(driver, 2).until(
                EC.element_to_be_clickable(
                    (By.CSS_SELECTOR, ".ecomerce-items-scroll-more")
                )
            )
            click_element(driver, more_link)
            time.sleep(1)
            retries = 0
        except TimeoutException:
            print("'More' button no longer found, exiting.")
            break
        except Exception as e:
            retries += 1
            print(f"Attempt {retries}: Error clicking 'More': {e}")
            time.sleep(1)
            if retries >= max_retries:
                print("Maximum retry attempts reached, exiting.")
                break


def get_rating_count(ratings_container: WebElement) -> int:
    try:
        paragraphs = ratings_container.find_elements(By.TAG_NAME, "p")
        if len(paragraphs) >= 2:
            spans = paragraphs[1].find_elements(By.TAG_NAME, "span")
            return len(spans)
        return 0
    except Exception as e:
        print(f"Error counting rating: {e}")
        return 0


def get_review_count(ratings_container: WebElement) -> int:
    try:
        first_paragraph = ratings_container.find_element(By.TAG_NAME, "p")
        review_text = first_paragraph.text.split(" ")
        return int(review_text[0]) if review_text else 0
    except Exception as e:
        print(f"Error retrieving review count: {e}")
        return 0


def extract_product_data(product_elem: WebElement) -> Product:
    title = product_elem.find_element(By.CSS_SELECTOR, ".title").get_attribute(
        "title"
    )
    description = product_elem.find_element(
        By.CSS_SELECTOR,
        ".description"
    ).text
    price = float(
        product_elem.find_element(By.CSS_SELECTOR, ".price").text.strip("$")
    )

    try:
        ratings_container = product_elem.find_element(
            By.CSS_SELECTOR,
            ".ratings"
        )
        rating = get_rating_count(ratings_container)
        reviews = get_review_count(ratings_container)
    except NoSuchElementException:
        rating = 0
        reviews = 0

    return Product(title, description, price, rating, reviews)


def save_to_csv(products: List[Product], filename: str) -> None:
    with open(filename, mode="w", newline='', encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(
            ["title", "description", "price", "rating", "num_of_reviews"]
        )
        for product in products:
            writer.writerow(product.to_csv_row())
    print(f"Data saved to {filename}")


def scrape_page(
        driver: webdriver.Chrome,
        url: str,
        csv_file_name: str
) -> None:
    driver.get(url)
    click_more_until_disappear(driver)

    try:
        WebDriverWait(driver, 15).until(
            lambda d: len(d.find_elements(By.CSS_SELECTOR, ".thumbnail")) > 0
        )
        time.sleep(2)
    except TimeoutException:
        print("Products not found on the page.")

    product_elements = driver.find_elements(By.CSS_SELECTOR, ".thumbnail")
    products = [extract_product_data(elem) for elem in product_elements]
    save_to_csv(products, csv_file_name)


def get_all_products() -> None:
    driver = create_driver()
    pages = [
        (HOME_URL, "home.csv"),
        (urljoin(BASE_URL, "test-sites/e-commerce/more/computers"),
         "computers.csv"),
        (urljoin(BASE_URL, "test-sites/e-commerce/more/phones"), "phones.csv"),
        (urljoin(BASE_URL, "test-sites/e-commerce/more/computers/laptops"),
         "laptops.csv"),
        (urljoin(BASE_URL, "test-sites/e-commerce/more/computers/tablets"),
         "tablets.csv"),
        (urljoin(BASE_URL, "test-sites/e-commerce/more/phones/touch"),
         "touch.csv")
    ]

    for url, csv_file_name in tqdm(pages, desc="Scraping Pages"):
        scrape_page(driver, url, csv_file_name)

    driver.quit()


if __name__ == "__main__":
    get_all_products()
