import csv
from dataclasses import dataclass, astuple
from urllib.parse import urljoin
from selenium import webdriver
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement


BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")
PRODUCT_FIELDS = ["title", "description", "price", "rating", "num_of_reviews"]


WEB_DRIVER: WebDriver | None = None


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


def parse_single_product(product_soup: WebElement) -> Product:
    count = 0
    for _ in product_soup.find_elements(By.CSS_SELECTOR, ".glyphicon-star"):
        count += 1
    return Product(
        title=product_soup.find_element(By.CLASS_NAME, "title").text,
        description=product_soup.find_element(
            By.CLASS_NAME,
            "description"
        ).text,
        price=float(product_soup.find_element(
            By.CLASS_NAME,
            "price"
        ).text.replace("$", "")),
        rating=count,
        num_of_reviews=int(product_soup.find_element(
            By.CSS_SELECTOR,
            "div.ratings > .pull-right"
        ).text.split()[0]),
    )


def get_page_products(path: str) -> list[Product]:
    url = urljoin(HOME_URL, path)

    driver = get_driver()
    driver.get(url)

    try:
        button = driver.find_element(
            By.CLASS_NAME,
            "ecomerce-items-scroll-more"
        )
        if button:
            while button.value_of_css_property("display") != "none":
                button.click()
    except Exception:
        pass

    products = driver.find_elements(By.CLASS_NAME, "thumbnail")

    return [parse_single_product(product) for product in products]


def get_driver() -> WebDriver:
    return WEB_DRIVER


def set_driver(new_driver: WebDriver) -> None:
    global WEB_DRIVER
    WEB_DRIVER = new_driver


def csv_file(path: str, products: list[Product]) -> None:
    if path == "":
        name = "home"
    else:
        path = path.split("/")
        path = [name for name in path if name]
        name = path[0] if len(path) == 1 else path[1]

    with open(
            "".join((name, ".csv")),
            "w",
            encoding="utf-8",
            newline=""
    ) as file:
        writer = csv.writer(file)
        writer.writerow(PRODUCT_FIELDS)
        writer.writerows([astuple(product) for product in products])


def get_all_products() -> None:
    urls = [
        "",
        "computers/",
        "phones/",
        "computers/laptops",
        "phones/touch",
        "computers/tablets"
    ]
    with webdriver.Chrome() as new_driver:
        set_driver(new_driver)
        driver = get_driver()
        driver.get(HOME_URL)

        cookies = driver.find_element(By.CLASS_NAME, "acceptCookies")
        cookies.click()
        for path in urls:
            csv_file(path, get_page_products(path))


if __name__ == "__main__":
    get_all_products()
