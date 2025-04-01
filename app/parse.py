import csv
from dataclasses import dataclass, fields, astuple
from urllib.parse import urljoin

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait
from tqdm import tqdm

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")
PAGE_PATHS = (
    ("", "home"),
    ("computers", "computers"),
    ("computers/laptops", "laptops"),
    ("computers/tablets", "tablets"),
    ("phones", "phones"),
    ("phones/touch", "touch"),
)

chrome_options = Options()
chrome_options.add_argument("--headless")


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


def create_product_instances(
        driver: webdriver.Chrome,
        product_cards: list[WebElement],
) -> list[Product]:
    result = []

    for card in product_cards:
        price = float(
            card.find_element(By.CLASS_NAME, "price").text.replace("$", "")
        )
        rating = len(
            card.find_elements(By.CSS_SELECTOR, ".ratings > p > span")
        )
        num_of_reviews = int(
            card.find_element(By.CLASS_NAME, "review-count").text.split()[0]
        )

        detail_card = card.find_element(By.CSS_SELECTOR, "a.title")
        detail_card.click()

        product = Product(
            title=driver.find_element(By.CLASS_NAME, "title").text,
            description=driver.find_element(By.CLASS_NAME, "description").text,
            price=price,
            rating=rating,
            num_of_reviews=num_of_reviews,
        )
        result.append(product)
        driver.back()

    return result


def write_to_csv(name_file: str, products: list[Product]) -> None:
    with open(name_file, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([field.name for field in fields(Product)])
        writer.writerows([astuple(product) for product in products])


def get_all_products() -> None:
    with webdriver.Chrome(options=chrome_options) as driver:
        accept_coki = False

        for page_path, name_product in tqdm(
                PAGE_PATHS,
                desc="Loading Products"
        ):
            driver.get(urljoin(HOME_URL, page_path))

            if not accept_coki:
                try:
                    accept_button = WebDriverWait(driver, 10).until(
                        expected_conditions.presence_of_element_located(
                            (By.CLASS_NAME, "acceptCookies")
                        )
                    )
                    accept_button.click()
                except Exception:
                    pass
                finally:
                    accept_coki = True

            while True:
                try:
                    button_more = driver.find_element(
                        By.CSS_SELECTOR,
                        ".btn.btn-lg.btn-block.btn-primary.ecomerce-items-scroll-more" # noqa
                    )
                    button_more.click()
                except Exception:
                    break
                finally:
                    driver.execute_script("window.scrollTo(0, 0);")

            product_cards = driver.find_elements(
                By.CLASS_NAME,
                "product-wrapper"
            )
            products = create_product_instances(driver, product_cards)
            write_to_csv(f"{name_product}.csv", products)


if __name__ == "__main__":
    get_all_products()
