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
TOUCh_URL = urljoin(PHONES_URL, "touch")


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


PRODUCT_FIELDS = [field.name for field in fields(Product)]

FILE_COLLECTION = {
    "home": "home.csv",
    "computers": "computers.csv",
    "laptops": "laptops.csv",
    "tablets": "tablets.csv",
    "phones": "phones.csv",
    "touches": "touch.csv",
}


def create_product(card: WebElement) -> Product | None:
    try:
        title_element = card.find_element(By.CLASS_NAME, "title")

        try:
            rating_val = card.find_element(
                By.CSS_SELECTOR,
                "p[data-rating]"
            ).get_attribute(
                "data-rating")
            rating = int(rating_val)
        except Exception:
            rating = len(card.find_elements(By.CLASS_NAME, "ws-icon-star"))

        try:
            reviews_text = card.find_element(By.CLASS_NAME,
                                             "review-count").text
            num_of_reviews = int(reviews_text.split()[0])
        except Exception:
            num_of_reviews = 0

        product = Product(
            title=title_element.get_attribute("title"),
            description=card.find_element(By.CLASS_NAME,
                                          "description").text,
            price=float(
                card.find_element(
                    By.CLASS_NAME, "price"
                ).text.replace("$", "")),
            rating=rating,
            num_of_reviews=num_of_reviews
        )
        return product

    except Exception as e:
        print(f"Skipping a product due to error: {e}")


def scrap_single_page(driver: webdriver.Chrome, url: str) -> list[Product]:
    driver.get(url)
    wait = WebDriverWait(driver, 5)

    try:
        wait.until(
            ec.presence_of_element_located((By.CLASS_NAME, "card-body")))
    except Exception:
        print(f"No products found on {url}. Skipping.")
        return []

    while True:
        try:
            current_count = len(
                driver.find_elements(By.CLASS_NAME, "card-body"))

            more_btn = wait.until(ec.element_to_be_clickable(
                (By.CLASS_NAME, "ecomerce-items-scroll-more")))

            if not more_btn.is_displayed():
                break

            driver.execute_script(
                "arguments[0].click();", more_btn
            )

            wait.until(lambda d: len(
                d.find_elements(By.CLASS_NAME, "card-body")) > current_count)

        except Exception:
            break

    product_cards = driver.find_elements(By.CLASS_NAME, "card-body")
    print(f"Finished loading {url}. Total items: {len(product_cards)}")

    return [create_product(card) for card in product_cards]


def write_products_to_csv(products: list[Product], file_name: str) -> None:
    with open(file_name, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(PRODUCT_FIELDS)
        writer.writerows([astuple(product) for product in products])


def get_all_products() -> None:
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )

    write_products_to_csv(
        products=scrap_single_page(driver=driver, url=HOME_URL),
        file_name=FILE_COLLECTION["home"]
    )
    write_products_to_csv(
        products=scrap_single_page(driver=driver, url=COMPUTERS_URL),
        file_name=FILE_COLLECTION["computers"]
    )
    write_products_to_csv(
        products=scrap_single_page(driver=driver, url=LAPTOPS_URL),
        file_name=FILE_COLLECTION["laptops"]
    )
    write_products_to_csv(
        products=scrap_single_page(driver=driver, url=TABLETS_URL),
        file_name=FILE_COLLECTION["tablets"]
    )
    write_products_to_csv(
        products=scrap_single_page(driver=driver, url=PHONES_URL),
        file_name=FILE_COLLECTION["phones"]
    )
    write_products_to_csv(
        products=scrap_single_page(driver=driver, url=TOUCh_URL),
        file_name=FILE_COLLECTION["touches"]
    )


if __name__ == "__main__":
    get_all_products()
