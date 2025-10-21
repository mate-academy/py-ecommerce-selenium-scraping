import csv
from dataclasses import dataclass
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from selenium.common import NoSuchElementException, ElementNotInteractableException
from selenium.webdriver.chrome.webdriver import WebDriver
from urllib.parse import urljoin


BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")
COMPUTERS_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/computers/")
LAPTOPS_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/computers/laptops")
TABLETS_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/computers/tablets")
PHONES_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/phones")
TOUCH_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/phones/touch")


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


def accept_cookies(driver: WebDriver) -> None:
    try:
        wait = WebDriverWait(driver, 5)
        button = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "acceptCookies")))
        button.click()
    except Exception:
        pass


def more_button(driver: WebDriver) -> None:
    try:
        while True:
            products_before = len(driver.find_elements(By.CSS_SELECTOR, ".card.thumbnail"))
            try:
                more = driver.find_element(By.CLASS_NAME, "ecomerce-items-scroll-more")
                if not more.is_displayed():
                    break
                more.click()
            except (NoSuchElementException, ElementNotInteractableException):
                break
            WebDriverWait(driver, 5).until(
                lambda d: len(d.find_elements(By.CSS_SELECTOR, ".card.thumbnail")) > products_before
            )
    except Exception:
        pass


def parse_page(driver: WebDriver, url: str) -> list[Product]:
    driver.get(url)
    accept_cookies(driver)
    WebDriverWait(driver, 5).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".card.thumbnail"))
    )
    try:
        driver.find_element(By.CLASS_NAME, "ecomerce-items-scroll-more")
        more_button(driver)
    except NoSuchElementException:
        pass
    products = driver.find_elements(By.CSS_SELECTOR, ".card.thumbnail")
    items = []
    for product in products:
        title = product.find_element(By.CLASS_NAME, "title").get_attribute("title")
        description = product.find_element(By.CSS_SELECTOR, ".card-text.description").text.strip()
        price = float(product.find_element(By.CSS_SELECTOR, ".price").text.replace("$", ""))
        rating_stars = product.find_elements(By.CSS_SELECTOR, ".ws-icon-star")
        rating = len(rating_stars)
        num_of_reviews = int(product.find_element(By.CSS_SELECTOR, "span[itemprop='reviewCount']").text)
        items.append(Product(title, description, price, rating, num_of_reviews))
    return items


def save_to_csv(filename: str, products: list[Product]) -> None:
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["title", "description", "price", "rating", "num_of_reviews"])
        for p in products:
            writer.writerow([p.title, p.description, p.price, p.rating, p.num_of_reviews])


def get_all_products() -> None:
    pages = {
        "home": HOME_URL,
        "computers": COMPUTERS_URL,
        "laptops": LAPTOPS_URL,
        "tablets": TABLETS_URL,
        "phones": PHONES_URL,
        "touch": TOUCH_URL,
    }
    driver = webdriver.Chrome()
    try:
        for page_name, url in pages.items():
            items = parse_page(driver, url)
            save_to_csv(f"{page_name}.csv", items)
    finally:
        driver.quit()


if __name__ == "__main__":
    get_all_products()
