import csv
import time
from dataclasses import dataclass, fields, astuple
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")

PAGES = {
    "home": HOME_URL,
    "computers": urljoin(BASE_URL, "test-sites/e-commerce/more/computers"),
    "laptops": urljoin(
        BASE_URL, "test-sites/e-commerce/more/computers/laptops"
    ),
    "tablets": urljoin(
        BASE_URL, "test-sites/e-commerce/more/computers/tablets"
    ),
    "phones": urljoin(BASE_URL, "test-sites/e-commerce/more/phones"),
    "touch": urljoin(BASE_URL, "test-sites/e-commerce/more/phones/touch"),
}


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


def accept_cookies(driver: webdriver.Chrome) -> None:
    time.sleep(2)
    try:
        accept_button = driver.find_element(
            By.XPATH, "//*[self::button or self::a][contains(text(), 'Accept')]"
        )
        accept_button.click()
        time.sleep(1)
    except NoSuchElementException:
        pass


def click_more_button(driver: webdriver.Chrome) -> None:
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as ec
    from selenium.common.exceptions import TimeoutException

    while True:
        try:
            more_button = WebDriverWait(driver, 3).until(
                ec.element_to_be_clickable(
                    (By.CLASS_NAME, "ecomerce-items-scroll-more")
                )
            )
        except TimeoutException:
            break

        more_button.click()
        time.sleep(0.3)


def parse_single_product(product_soup: BeautifulSoup) -> Product:
    description = product_soup.select_one(".description").get_text(strip=True)

    return Product(
        title=product_soup.select_one(".title")["title"],
        description=description.replace("\xa0", " "),
        price=float(
            product_soup.select_one(".price").get_text(strip=True).replace("$", "")
        ),
        rating=len(product_soup.select(".ws-icon-star")),
        num_of_reviews=int(
            product_soup.select_one(".review-count").get_text().split()[0]
        ),
    )


def get_single_page_products(
        driver: webdriver.Chrome, url: str
) -> list[Product]:
    driver.get(url)
    click_more_button(driver)

    soup = BeautifulSoup(driver.page_source, "html.parser")
    product_cards = soup.select(".product-wrapper")

    return [parse_single_product(card) for card in product_cards]


def write_products_to_csv(products: list[Product], path: str) -> None:
    with open(path, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow([field.name for field in fields(Product)])
        writer.writerows([astuple(product) for product in products])


def get_all_products() -> None:
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--window-size=1920,1080")
    driver = webdriver.Chrome(options=options)
    driver.implicitly_wait(5)

    driver.get(HOME_URL)
    accept_cookies(driver)

    for name, url in PAGES.items():
        products = get_single_page_products(driver, url)
        write_products_to_csv(products, f"{name}.csv")

    driver.quit()


if __name__ == "__main__":
    get_all_products()