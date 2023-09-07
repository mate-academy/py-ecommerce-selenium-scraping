import time
from dataclasses import dataclass
from urllib.parse import urljoin
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import csv
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


def rating_stars_count(rating_element):
    return len(
        rating_element.find_elements(
            By.TAG_NAME, "p"
        )[1].find_elements(
            By.TAG_NAME, "span"
        )
    )


def get_product_info(product_element):
    title = product_element.find_element(By.CLASS_NAME, "title").text
    description = product_element.find_element(
        By.CLASS_NAME,
        "description"
    ).text
    price = float(
        product_element.find_element(
            By.CLASS_NAME, "price"
        ).text.replace("$", "").replace(",", ""))
    rating_element = product_element.find_element(By.CLASS_NAME, "ratings")
    rating = rating_stars_count(rating_element)
    num_of_reviews = int(
        rating_element.find_element(
            By.CLASS_NAME, "pull-right"
        ).text.split()[0]
    )
    return Product(
        title=title,
        description=description,
        price=price,
        rating=rating,
        num_of_reviews=num_of_reviews
    )


def scrape_page(url, filename):
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    driver = webdriver.Chrome(options=options)

    driver.get(url)

    try:
        accept_cookies_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "cookie-law-button")))
        accept_cookies_button.click()
    except:
        pass

    products = []
    while True:
        product_elements = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, "thumbnail")))

        for product_element in product_elements:
            products.append(get_product_info(product_element))

        try:
            more_button = driver.find_element(By.CLASS_NAME, "ecomerce-items-scroll-more")
            more_button.click()
            time.sleep(5)
        except:
            break

    with open(filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(
            ["Title", "Description", "Price", "Rating", "Number of Reviews"])
        for product in products:
            writer.writerow([product.title, product.description, product.price,
                             product.rating, product.num_of_reviews])

    driver.quit()


def get_all_products():
    page_info = [
        (HOME_URL, "home.csv"),
        (urljoin(BASE_URL, "test-sites/e-commerce/more/computers"),
         "computers.csv"),
        (urljoin(BASE_URL, "test-sites/e-commerce/more/computers/laptops"),
         "laptops.csv"),
        (urljoin(BASE_URL, "test-sites/e-commerce/more/computers/tablets"),
         "tablets.csv"),
        (urljoin(BASE_URL, "test-sites/e-commerce/more/phones"), "phones.csv"),
        (urljoin(BASE_URL, "test-sites/e-commerce/more/phones/touch"),
         "touch.csv")
    ]

    for url, filename in tqdm(page_info, desc="Scraping pages"):
        scrape_page(url, filename)


if __name__ == "__main__":
    get_all_products()
