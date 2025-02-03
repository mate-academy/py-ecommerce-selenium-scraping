import csv
from dataclasses import dataclass, fields, astuple
from time import sleep
from urllib.parse import urljoin

from bs4 import BeautifulSoup, Tag
from selenium import webdriver
from selenium.common import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.wait import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support import expected_conditions as ec


BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")
COMPUTERS_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/computers/")
LAPTOPS_URL = urljoin(
    BASE_URL,
    "test-sites/e-commerce/more/computers/laptops",
)
TABLETS_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/computers/tablets")
PHONES_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/phones/")
TOUCH_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/phones/touch")

URLS_AND_FILENAMES = [
    (HOME_URL, "home.csv"),
    (COMPUTERS_URL, "computers.csv"),
    (LAPTOPS_URL, "laptops.csv"),
    (TABLETS_URL, "tablets.csv"),
    (PHONES_URL, "phones.csv"),
    (TOUCH_URL, "touch.csv"),
]


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


PRODUCT_FIELDS = [field.name for field in fields(Product)]


def setup_driver() -> webdriver:
    print("Setting up the Chrome driver...")

    options = webdriver.ChromeOptions()

    options.add_argument("--headless")
    print("Headless mode enabled.")

    driver_path = ChromeDriverManager().install()
    print(f"Using ChromeDriver from: {driver_path}")

    driver = webdriver.Chrome(service=Service(driver_path), options=options)

    print("Chrome driver setup complete.")
    return driver


def parse_more_button(driver: webdriver) -> None:
    try:
        more_button = WebDriverWait(driver, 5).until(
            ec.element_to_be_clickable(
                (By.CLASS_NAME, "ecomerce-items-scroll-more")
            )
        )

        while more_button.is_displayed():
            more_button.click()
            print("Clicked 'More', waiting for new products to load...")
            sleep(0.5)

    except TimeoutException:
        print("Timed out: 'More' button not found within the time limit.")
    except Exception as e:
        print(f"No 'More' button found or other error: {e}")


def get_page_products(page_soup: Tag) -> [Product]:
    print("Extracting products from the current page...")
    products = page_soup.select(".card-body")
    return [parse_single_product(product) for product in products]


def parse_single_product(product: Tag) -> Product:
    print("Using parse_single_product function...")

    title_element = product.select_one(".title")
    title = title_element["title"] if title_element else None
    print(f"Title: {title}")

    description_element = product.select_one(".description")
    description = (
        description_element.text.strip() if description_element else None
    )
    print(f"Description: {description}")

    price_element = product.select_one(".price")
    price = (
        float(price_element.text.replace("$", "").strip())
        if price_element
        else None
    )
    print(f"Price: {price}")

    rating_element = product.select_one(".ratings p[data-rating]")
    rating = int(rating_element.get("data-rating")) if rating_element else None
    print(f"Rating: {rating}")

    review_count_element = product.select_one(".review-count")
    num_of_reviews = (
        int(review_count_element.text.split()[0])
        if review_count_element
        else None
    )
    print(f"Number of reviews: {num_of_reviews}")

    return Product(
        title=title,
        description=description,
        price=price,
        rating=rating,
        num_of_reviews=num_of_reviews,
    )


def get_all_products() -> [Product]:
    all_products = []

    for url, filename in URLS_AND_FILENAMES:
        print(f"Setting up the driver for URL: {url}")
        driver = setup_driver()
        driver.get(url)

        print("Starting to click 'More' buttons...")
        parse_more_button(driver)
        sleep(1)

        while True:
            print("Fetching products from page...")

            page_source = driver.page_source
            soup = BeautifulSoup(page_source, "html.parser")
            page_products = get_page_products(soup)

            if not page_products:
                break

            all_products.extend(page_products)

        print(f"Total products scraped from {url}: {len(all_products)}")
        driver.quit()

    return all_products


def write_products_to_csv(products: [Product], filename: str) -> None:
    print(f"Writing products to {filename}...")

    with open(filename, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(PRODUCT_FIELDS)

        for product in products:
            clean_product = [
                "" if value is None else value for value in astuple(product)
            ]
            writer.writerow(clean_product)

    print(f"Finished writing products to {filename}.")


def scrape_and_save() -> None:
    for url, filename in URLS_AND_FILENAMES:
        print(f"Scraping {filename} page...")
        products = get_all_products()
        write_products_to_csv(products, filename)
        print(f"Finished scraping and saved to {filename}.\n")


if __name__ == "__main__":
    scrape_and_save()
