import csv
from dataclasses import dataclass, fields, astuple
from urllib.parse import urljoin

from bs4 import BeautifulSoup, Tag
from selenium import webdriver
from selenium.common import TimeoutException, WebDriverException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions
from tqdm import tqdm

options = Options()
options.add_argument("--headless")
_driver: WebDriver | None = None


def get_driver() -> WebDriver:
    return _driver


def set_driver(new_driver: WebDriver) -> None:
    global _driver
    _driver = new_driver


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


PRODUCT_COLUMNS = [field.name for field in fields(Product)]


def parse_single_product(soup: Tag) -> Product:
    return Product(
        title=soup.select_one("a[itemprop='name']")["title"],
        description=soup.select_one("p[itemprop='description']")
        .get_text()
        .replace("\xa0", " "),
        price=float(soup.select_one(".price").text.replace("$", "")),
        rating=len(soup.find_all("span", class_="ws-icon ws-icon-star")),
        num_of_reviews=int(
            soup.select_one(".review-count > span[itemprop=reviewCount]")
            .text
        ),
    )


def scrape_page(url: str) -> list[Product]:
    driver = get_driver()
    driver.get(url)

    try:
        WebDriverWait(driver, 3).until(
            expected_conditions.element_to_be_clickable(
                (By.CSS_SELECTOR, 'button[data-tid="banner-accept"]')
            )
        ).click()
    except TimeoutException:
        pass

    while True:
        try:
            more_button = WebDriverWait(driver, 2).until(
                expected_conditions.element_to_be_clickable(
                    (By.CLASS_NAME, "ecomerce-items-scroll-more")
                )
            )
            more_button.click()
        except WebDriverException:
            break

    html = driver.page_source
    soup = BeautifulSoup(html, "html.parser")
    products_soup = soup.find_all("div", class_="product-wrapper")

    return [parse_single_product(soup) for soup in products_soup]


def save_to_csv(filename: str, products: list[Product]) -> None:
    with open(filename, "w") as f:
        writer = csv.writer(f)
        writer.writerow(PRODUCT_COLUMNS)
        writer.writerows(astuple(product) for product in products)


def get_all_products() -> None:
    pages = {
        "home.csv": HOME_URL,
        "computers.csv": COMPUTERS_URL,
        "laptops.csv": LAPTOPS_URL,
        "tablets.csv": TABLETS_URL,
        "phones.csv": PHONES_URL,
        "touch.csv": TOUCH_URL,
    }

    with webdriver.Chrome(options=options) as driver:
        set_driver(driver)

        for filename, url in tqdm(pages.items()):
            products = scrape_page(url)
            save_to_csv(filename, products)


if __name__ == "__main__":
    get_all_products()
