from dataclasses import dataclass
from urllib.parse import urljoin
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.common.exceptions import NoSuchElementException, TimeoutException
import csv
from tqdm import tqdm
from typing import List

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")

PAGES_TO_SCRAPE = {
    "home": HOME_URL,
    "computers": urljoin(HOME_URL, "computers"),
    "laptops": urljoin(HOME_URL, "computers/laptops"),
    "tablets": urljoin(HOME_URL, "computers/tablets"),
    "phones": urljoin(HOME_URL, "phones"),
    "touch": urljoin(HOME_URL, "phones/touch"),
}


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


def setup_driver() -> webdriver.Chrome:
    chrome_options = Options()
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--headless")

    try:
        driver = webdriver.Chrome(options=chrome_options)
        driver.implicitly_wait(0)
        return driver
    except Exception as e:
        print(f"[ERROR] driver hasn't been initialized: {e}")
        raise


def save_to_csv(filename: str, products: List[Product]) -> None:
    filepath = f"{filename}.csv"
    try:
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["title", "description", "price",
                             "rating", "num_of_reviews"])

            for product in products:
                writer.writerow([product.title, product.description,
                                 product.price, product.rating,
                                 product.num_of_reviews])
        print(f"[INFO] saved {len(products)} products to {filepath}")
    except IOError as e:
        print(f"[ERROR] Could not write to {filepath}: {e}")


def handle_cookies(driver: webdriver.Chrome, wait: WebDriverWait) -> None:
    cookie_button_selector = "button.acceptCookies"
    locator = (By.CSS_SELECTOR, cookie_button_selector)
    try:
        wait.until(expected_conditions.element_to_be_clickable(
            locator)).click()
        print("[INFO] cookie was clicked")
        wait.until(expected_conditions.
                   invisibility_of_element_located(locator))
    except Exception:
        pass


def scrape_single_page(driver: webdriver.Chrome,
                       url: str, filename: str) -> None:
    driver.get(url)
    wait = WebDriverWait(driver, 15)
    handle_cookies(driver, wait)

    product_cards_selector = "div.product-wrapper.card-body"
    long_wait = WebDriverWait(driver, 20)

    try:
        first_product = long_wait.until(
            expected_conditions.presence_of_element_located(
                (By.CSS_SELECTOR, product_cards_selector)
            )
        )
        driver.execute_script("arguments[0].scrollIntoView(true);",
                              first_product)
        print("[INFO] Scroll to products is done")

    except TimeoutException:
        print(f"[WARNING] TimeOut: Products not loaded for {url}. Skipping.")
        save_to_csv(filename, [])
        return

    more_button_selector = "a.btn-primary.ecomerce-items-scroll-more"

    while True:
        try:
            more_button = WebDriverWait(driver, 5).until(
                expected_conditions.element_to_be_clickable(
                    (By.CSS_SELECTOR, more_button_selector)
                )
            )

            if not more_button.is_displayed():
                break

            old_count = len(driver.find_elements(By.CSS_SELECTOR,
                                                 product_cards_selector))

            driver.execute_script("arguments[0].scrollIntoView(true);",
                                  more_button)
            driver.execute_script("arguments[0].click();", more_button)

            long_wait.until(
                lambda d: len(d.find_elements(
                    By.CSS_SELECTOR,
                    product_cards_selector)) > old_count
            )

        except (TimeoutException, Exception):
            # Pagination ends when button is no longer clickable/visible
            break

    long_wait.until(expected_conditions.presence_of_all_elements_located(
        (By.CSS_SELECTOR, product_cards_selector)))
    product_elements = driver.find_elements(By.CSS_SELECTOR,
                                            product_cards_selector)

    products = []

    for card in tqdm(product_elements, desc=f"[Parse] {filename}", leave=False):
        try:
            title = card.find_element(By.CSS_SELECTOR, "a.title").text
            description = card.find_element(By.CSS_SELECTOR,
                                            "p.description").text

            price_text = None
            try:
                price_element = card.find_element(By.CSS_SELECTOR,
                                                  "h4.price span")
                price_text = price_element.text
            except NoSuchElementException:
                price_element = card.find_element(By.CSS_SELECTOR, "h4.price")
                price_text = price_element.text

            price = float(price_text.replace("$", ""))

            try:
                rating_container = card.find_element(By.CSS_SELECTOR,
                                                     "p[data-rating]")
                rating_int = int(rating_container.get_attribute("data-rating"))
            except NoSuchElementException:
                rating_int = 0

            try:
                reviews_text = card.find_element(
                    By.CSS_SELECTOR,
                    "p.review-count").text.split()[0]
                num_of_reviews = int(reviews_text)
            except (NoSuchElementException, IndexError, ValueError):
                num_of_reviews = 0

            products.append(Product(
                title=title,
                description=description,
                price=price,
                rating=rating_int,
                num_of_reviews=num_of_reviews,
            ))

        except Exception:
            continue

    save_to_csv(filename, products)


def get_all_products() -> None:
    driver = None
    try:
        driver = setup_driver()
        for filename, url in PAGES_TO_SCRAPE.items():
            print(f"[INFO] scraping {filename}")
            scrape_single_page(driver, url, filename)
    except Exception as e:
        print(f"[ERROR] Global error: {e}")
    finally:
        if driver:
            driver.quit()
            print("[INFO] driver has been closed")


if __name__ == "__main__":
    get_all_products()
