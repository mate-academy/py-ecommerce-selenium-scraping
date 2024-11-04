import csv
import time
from dataclasses import dataclass, asdict
from urllib.parse import urljoin

from selenium import webdriver
from selenium.common import (
    NoSuchElementException,
    ElementNotInteractableException,
    ElementClickInterceptedException,
)
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement

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


def scrape_single_product(product: WebElement) -> Product:
    title = product.find_element(By.CLASS_NAME, "title").get_attribute("title")
    price, _, description, num_of_reviews = product.text.split("\n")
    price = float(price.replace("$", ""))
    num_of_reviews = int(num_of_reviews.split()[0])

    rating = (
        product.find_element(By.CLASS_NAME, "ratings")
        .find_elements(By.TAG_NAME, "p")[-1]
        .get_attribute("data-rating")
    )

    rating = int(rating) if rating else 5

    return Product(
        title=title,
        price=price,
        description=description,
        num_of_reviews=num_of_reviews,
        rating=rating,
    )


def scrape_page(url: str, driver: WebDriver) -> list[Product]:
    driver.get(url)

    try:
        if accept := driver.find_element(By.CLASS_NAME, "acceptCookies"):
            time.sleep(0.5)
            accept.click()

    except NoSuchElementException:
        pass

    try:
        while more := driver.find_element(
                By.CLASS_NAME, "ecomerce-items-scroll-more"
        ):
            if not more.is_displayed():
                break
            more.click()

    except (
        NoSuchElementException,
        ElementNotInteractableException,
        ElementClickInterceptedException,
    ):
        pass

    products = driver.find_elements(By.CLASS_NAME, "card-body")

    return [scrape_single_product(product) for product in products]


def get_urls(class_name: str, driver: WebDriver) -> list[tuple]:
    return [
        (elem.text.lower(), elem.get_attribute("href"))
        for elem in driver.find_elements(By.CLASS_NAME, class_name)
    ]


def get_sidebar_urls(home_url: str, driver: WebDriver) -> list[tuple | tuple[str, str]]:
    driver.get(home_url)
    categories = get_urls("category-link", driver)

    subcategories = []
    for _, url in categories:
        driver.get(url)
        subcategories.extend(get_urls("subcategory-link", driver))

    return [("home", home_url)] + categories + subcategories


def write_to_csv(filename: str, products: list[Product]) -> None:
    with open(filename, "w", newline="") as csvfile:
        fields = ("title", "description", "price", "rating", "num_of_reviews")
        writer = csv.DictWriter(csvfile, fieldnames=fields)
        writer.writeheader()

        for product in products:
            writer.writerow(asdict(product))


def get_all_products() -> None:
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    driver = webdriver.Chrome(options=options)

    urls = get_sidebar_urls(HOME_URL, driver)

    for tab_name, url in tqdm(urls):
        page = scrape_page(url, driver)
        write_to_csv(f"{tab_name}.csv", page)

    driver.quit()


if __name__ == "__main__":
    print("Running selenium scraper...")
    get_all_products()
    print("Done!")
