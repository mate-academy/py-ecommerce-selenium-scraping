import csv
from dataclasses import dataclass, fields, astuple
from urllib.parse import urljoin

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.wait import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support import expected_conditions as ec

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")
COMPUTERS_URL = urljoin(HOME_URL, "computers/")
LAPTOPS_URL = urljoin(COMPUTERS_URL, "laptops")
TABLETS_URL = urljoin(COMPUTERS_URL, "tablets")
PHONES_URL = urljoin(HOME_URL, "phones/")
TOUCH_URL = urljoin(PHONES_URL, "touch")


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


PRODUCT_FIELDS = [field.name for field in fields(Product)]

FILE_COLLECTION = {
    "home.csv": HOME_URL,
    "computers.csv": COMPUTERS_URL,
    "laptops.csv": LAPTOPS_URL,
    "tablets.csv": TABLETS_URL,
    "phones.csv": PHONES_URL,
    "touch.csv": TOUCH_URL,
}


def create_product(card: WebElement) -> Product | None:
    try:
        title_element = card.find_element(By.CLASS_NAME, "title")
        title = title_element.get_attribute("title")
        if not title:
            title = title_element.text

        description = card.find_element(By.CLASS_NAME, "description").text

        price_text = card.find_element(By.CLASS_NAME, "price").text
        clean_price = "".join(c for c in price_text if c.isdigit() or c == ".")
        price = float(clean_price) if clean_price else 0.0

        rating = len(card.find_elements(By.CLASS_NAME, "ws-icon-star"))

        num_of_reviews = 0
        try:
            ratings = card.find_element(By.CLASS_NAME, "ratings")
            paragraphs = ratings.find_elements(By.TAG_NAME, "p")
            for p in paragraphs:
                if "reviews" in p.text:
                    num_of_reviews = int(p.text.split()[0])
                    break
        except Exception:
            pass

        return Product(
            title=title,
            description=description,
            price=price,
            rating=rating,
            num_of_reviews=num_of_reviews
        )

    except Exception:
        return None


def scrap_single_page(driver: webdriver.Chrome, url: str) -> list[Product]:
    driver.get(url)
    wait = WebDriverWait(driver, 10)

    try:
        cookie_btn = wait.until(
            ec.element_to_be_clickable((By.CLASS_NAME, "acceptCookies"))
        )
        cookie_btn.click()
    except Exception:
        pass

    try:
        wait.until(
            ec.presence_of_element_located((By.CLASS_NAME, "thumbnail"))
        )
    except Exception:
        return []

    while True:
        try:
            cards = driver.find_elements(By.CLASS_NAME, "thumbnail")
            current_count = len(cards)

            more_btn = driver.find_element(By.CLASS_NAME,
                                           "ecomerce-items-scroll-more")

            if not more_btn.is_displayed():
                break

            driver.execute_script("arguments[0].scrollIntoView();", more_btn)
            driver.execute_script("arguments[0].click();", more_btn)

            wait.until(lambda d: len(
                d.find_elements(By.CLASS_NAME, "thumbnail")) > current_count
                       )

        except Exception:
            break

    product_cards = driver.find_elements(By.CLASS_NAME, "thumbnail")
    products = (create_product(card) for card in product_cards)
    return [p for p in products if p]


def write_products_to_csv(products: list[Product], file_name: str) -> None:
    with open(file_name, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(PRODUCT_FIELDS)
        writer.writerows([astuple(product) for product in products])


def get_all_products() -> None:
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )

    try:
        for file_name, url in FILE_COLLECTION.items():
            products = scrap_single_page(driver=driver, url=url)
            write_products_to_csv(products=products, file_name=file_name)
    finally:
        driver.quit()


if __name__ == "__main__":
    get_all_products()
