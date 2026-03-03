import csv
from time import sleep
from bs4 import BeautifulSoup, Tag
from selenium import webdriver
from dataclasses import dataclass, fields, astuple
from urllib.parse import urljoin
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By

_driver: WebDriver | None = None


def get_driver() -> WebDriver:
    return _driver


def set_driver(new_driver: WebDriver) -> None:
    global _driver
    _driver = new_driver


BASE_URL = "https://webscraper.io/test-sites/e-commerce/more/"
PREF_LIST = [
    "",
    "computers",
    "computers/laptops",
    "computers/tablets",
    "phones",
    "phones/touch",
]


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


FIELDS = [field.name for field in fields(Product)]


def serializer(product: Tag) -> Product:
    title = product.select_one(".title")["title"]
    description = (product
                   .select_one(".description")
                   .get_text(strip=True)
                   .replace("\xa0", " ")
                   )
    price_str = product.select_one(".price").string.replace("$", "")
    rating = len(product.select(".ws-icon-star"))
    num_of_reviews = product.select_one(".review-count > span").string
    return Product(
        title=title,
        description=description,
        price=float(price_str),
        rating=rating,
        num_of_reviews=int(num_of_reviews),
    )


def write_to_file(products: list[Product], path_csv: str) -> None:
    with open(path_csv, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(FIELDS)
        writer.writerows([astuple(product) for product in products])


def scrape(url: str, path_csv: str) -> list[Product]:
    products = []
    driver = get_driver()
    driver.get(url)
    cookie = driver.find_elements(By.CLASS_NAME, "acceptCookies")
    if cookie:
        cookie[0].click()
    while True:
        button = driver.find_elements(By.CSS_SELECTOR, "a.btn-block")
        if not button or not button[0].is_displayed():
            break
        button[0].click()
        sleep(0.2)

    soup = BeautifulSoup(driver.page_source, "html.parser")
    items = soup.select(".ecomerce-items > div")
    products += [serializer(item) for item in items]

    write_to_file(products=products, path_csv=path_csv)
    return products


def get_all_products() -> None:
    with webdriver.Chrome() as driver:
        set_driver(driver)
        for pref in PREF_LIST:
            url = urljoin(BASE_URL, pref)
            if pref == "":
                path_csv = "home.csv"
            else:
                path_csv = pref.split("/")[-1] + ".csv"
            scrape(url=url, path_csv=path_csv)


if __name__ == "__main__":
    get_all_products()
