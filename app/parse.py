import csv
from dataclasses import dataclass
from urllib.parse import urljoin
from selenium import webdriver
from selenium.common import TimeoutException, NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


def parse_single_product(product: WebElement) -> Product:
    rating_elements = product.find_elements(By.CSS_SELECTOR, "span.ws-icon")
    rating = len(rating_elements)
    return Product(
        title=product.find_element(By.CLASS_NAME,
                                   "title").get_attribute("title"),
        description=product.find_element(By.CLASS_NAME,
                                         "description").text,
        price=float(product.find_element(By.CLASS_NAME,
                                         "price").text.replace("$", "")),
        rating=rating,
        num_of_reviews=int(product.find_element(By.CLASS_NAME,
                                        "review-count").text.split()[0])
    )


def scrape(driver: webdriver.Chrome, url: str) -> list[Product]:
    driver.get(url)

    WebDriverWait(driver, 10).until(ec.presence_of_element_located(
        (By.CLASS_NAME, "thumbnail")))

    while True:
        try:
            button = WebDriverWait(driver, 10).until(
                ec.element_to_be_clickable((By.CSS_SELECTOR, ".ecomerce-items-scroll-more"))
            )
            driver.execute_script("arguments[0].click();", button)

            WebDriverWait(driver, 10).until(
                ec.presence_of_all_elements_located((By.CLASS_NAME, "thumbnail"))
            )


        except (TimeoutException, NoSuchElementException):
            break

    cards = driver.find_elements(By.CLASS_NAME, "thumbnail")
    products = [parse_single_product(card) for card in cards]

    return products


def write_to_csv(products: list[Product], filename: str) -> None:
    with open(filename, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["title", "description",
                         "price", "rating", "num_of_reviews"])
        for product in products:
            writer.writerow([product.title, product.description, product.price,
                             product.rating, product.num_of_reviews])


def get_all_products() -> None:
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    driver = webdriver.Chrome(options=options)

    pages = {
        "home.csv": HOME_URL,
        "computers.csv": urljoin(HOME_URL, "computers"),
        "laptops.csv": urljoin(HOME_URL, "computers/laptops"),
        "tablets.csv": urljoin(HOME_URL, "computers/tablets"),
        "phones.csv": urljoin(HOME_URL, "phones"),
        "touch.csv": urljoin(HOME_URL, "phones/touch"),
    }

    for filename, url in pages.items():
        print(f"Scraping {url}...")
        products = scrape(driver, url)
        write_to_csv(products, filename)
        print(f"Saved {len(products)} products to {filename}")

    driver.quit()


if __name__ == "__main__":
    get_all_products()
