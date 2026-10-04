import csv
from dataclasses import dataclass, fields, astuple
from urllib.parse import urljoin
from bs4 import BeautifulSoup, Tag
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC  # noqa: N812

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")
LAPTOP_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/computers/laptops")
COMPUTER_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/computers")
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


PRODUCT_FIELDS = [field.name for field in fields(Product)]


def parse_single_product(product: Tag) -> Product:
    return Product(
        title=product.select_one(".title")["title"],
        description=product
        .select_one(".description")
        .text.replace("\xa0", " "),
        price=float(product.select_one(".price").text.replace("$", "")),
        rating=len(product.select(".ws-icon-star")),
        num_of_reviews=int(product.select_one(".review-count")
                           .text.split(" ")[0]),
    )


def get_products(url: str) -> list[Product]:
    driver = webdriver.Chrome()

    try:
        driver.get(url)

        try:
            decline = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable(
                    (By.CSS_SELECTOR, '[data-tid="banner-decline"]')
                )
            )
            decline.click()
        except Exception:
            pass

        while True:
            more_buttons = driver.find_elements(
                By.CLASS_NAME,
                "ecomerce-items-scroll-more"
            )

            if not more_buttons or not more_buttons[0].is_displayed():
                break

            old_count = len(
                driver.find_elements(By.CSS_SELECTOR, ".card-body")
            )

            more_buttons[0].click()

            WebDriverWait(driver, 10).until(
                lambda d: len(
                    d.find_elements(By.CSS_SELECTOR, ".card-body")
                ) > old_count
            )

        soup = BeautifulSoup(driver.page_source, "html.parser")
        products = soup.select(".card-body")

        return [parse_single_product(product) for product in products]

    finally:
        driver.quit()


def write_results_to_csv(filename: str, products: list[Product]) -> None:
    with open(filename, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(PRODUCT_FIELDS)
        writer.writerows([astuple(product) for product in products])


def get_all_products() -> None:
    filenames_and_urls = [
        ("home.csv", HOME_URL),
        ("computers.csv", COMPUTER_URL),
        ("laptops.csv", LAPTOP_URL),
        ("tablets.csv", TABLETS_URL),
        ("phones.csv", PHONES_URL),
        ("touch.csv", TOUCH_URL),
    ]
    for filename, url in filenames_and_urls:
        products = get_products(url)
        print(products)
        write_results_to_csv(filename, products)


if __name__ == "__main__":
    get_all_products()
