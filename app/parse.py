from dataclasses import dataclass
from urllib.parse import urljoin
import csv
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from tqdm import tqdm

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


def handle_cookies(driver):
    try:
        accept_button = WebDriverWait(driver, 3).until(
            EC.element_to_be_clickable((By.CLASS_NAME, "acceptCookies"))
        )
        accept_button.click()
    except TimeoutException:
        pass


def scrape_page(driver, url, filename, has_pagination=False):
    driver.get(url)
    handle_cookies(driver)

    if has_pagination:
        while True:
            try:
                more_button = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.ID, "more"))
                )
                if more_button.get_attribute("disabled"):
                    break
                more_button.click()
                try:
                    WebDriverWait(driver, 5).until(
                        EC.visibility_of_element_located((By.ID, "loading"))
                    )
                    WebDriverWait(driver, 10).until(
                        EC.invisibility_of_element_located((By.ID, "loading"))
                    )
                except TimeoutException:
                    time.sleep(1)
            except (TimeoutException, NoSuchElementException):
                break

    products = []
    thumbnails = driver.find_elements(By.CLASS_NAME, "thumbnail")

    for thumb in thumbnails:
        try:
            title = thumb.find_element(By.CLASS_NAME, "title").get_attribute("title")
        except NoSuchElementException:
            title = thumb.find_element(By.CLASS_NAME, "title").text

        try:
            description = thumb.find_element(By.CLASS_NAME, "description").text
        except NoSuchElementException:
            description = "N/A"

        try:
            price_text = thumb.find_element(By.CLASS_NAME, "price").text
            price = float(price_text.replace('$', '').replace(',', ''))
        except (NoSuchElementException, ValueError):
            price = 0.0

        try:
            rating = int(thumb.find_element(By.CSS_SELECTOR, ".ratings p").get_attribute("data-rating"))
        except (NoSuchElementException, ValueError):
            rating = 0

        try:
            reviews_text = thumb.find_element(By.CSS_SELECTOR, ".ratings .pull-right").text
            num_of_reviews = int(reviews_text.split()[0])
        except (NoSuchElementException, IndexError, ValueError):
            num_of_reviews = 0

        products.append(Product(title, description, price, rating, num_of_reviews))

    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Title', 'Description', 'Price', 'Rating', 'Number of Reviews'])
        for p in products:
            writer.writerow([p.title, p.description, p.price, p.rating, p.num_of_reviews])


def get_all_products():
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    driver = webdriver.Chrome(options=options)

    pages = [
        {'name': 'home', 'url': HOME_URL, 'pagination': False},
        {'name': 'computers', 'url': urljoin(BASE_URL, "test-sites/e-commerce/more/computers"), 'pagination': False},
        {'name': 'laptops', 'url': urljoin(BASE_URL, "test-sites/e-commerce/more/computers/laptops"),
         'pagination': True},
        {'name': 'tablets', 'url': urljoin(BASE_URL, "test-sites/e-commerce/more/computers/tablets"),
         'pagination': True},
        {'name': 'phones', 'url': urljoin(BASE_URL, "test-sites/e-commerce/more/phones"), 'pagination': False},
        {'name': 'touch', 'url': urljoin(BASE_URL, "test-sites/e-commerce/more/phones/touch"), 'pagination': True},
    ]

    for page in tqdm(pages, desc="Scraping pages"):
        scrape_page(
            driver,
            page['url'],
            f"{page['name']}.csv",
            page['pagination']
        )

    driver.quit()


if __name__ == "__main__":
    get_all_products()