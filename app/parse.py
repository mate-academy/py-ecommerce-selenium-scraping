import csv
from dataclasses import dataclass
from urllib.parse import urljoin
from bs4 import BeautifulSoup
import selenium
from selenium.common import NoSuchElementException
from selenium.webdriver.common.by import By


HOME_URL = "https://webscraper.io/test-sites/e-commerce/more/"
URLS = {
    "home": HOME_URL,
    "computers": urljoin(HOME_URL, "computers/"),
    "laptops": urljoin(HOME_URL, "computers/laptops"),
    "tablets": urljoin(HOME_URL, "computers/tablets"),
    "phones": urljoin(HOME_URL, "phones/"),
    "touch": urljoin(HOME_URL, "phones/touch")
}


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


def parse_single_product(product_soup: BeautifulSoup) -> Product:
    return Product(
        title=product_soup.select_one(".title")["title"],
        description=product_soup.select_one(".description").text,
        price=float(product_soup.select_one(
            ".price"
        ).text.replace("$", "")),
        rating=len(product_soup.select(".ws-icon-star")),
        num_of_reviews=int(product_soup.select_one(
            ".ratings > .pull-right"
        ).text.split()[0])
    )


def get_full_page(driver: selenium.webdriver.Chrome) -> BeautifulSoup:
    try:
        button_more = driver.find_element(
            By.CLASS_NAME, "ecomerce-items-scroll-more"
        )
        while button_more and button_more.is_displayed():
            button_more.click()
    except NoSuchElementException:
        pass
    finally:
        return BeautifulSoup(driver.page_source, "html.parser")


def get_products_from_page(driver: selenium.webdriver.Chrome) -> [Product]:
    soup = get_full_page(driver=driver)
    products = soup.select(".thumbnail")
    return [parse_single_product(product_soup) for product_soup in products]


def write_files(product_name: str, products: [Product]) -> None:
    csv_path = f"{product_name}.csv"
    with open(csv_path, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(
            ["title", "description", "price", "rating", "num_of_reviews"]
        )
        for product in products:
            writer.writerow([
                product.title,
                product.description,
                product.price,
                product.rating,
                product.num_of_reviews
            ])


def get_all_products() -> None:
    driver = selenium.webdriver.Chrome()
    for product_name, url in URLS.items():
        driver.get(url)
        try:
            accept_cookies = driver.find_element(
                By.CLASS_NAME, "acceptCookies"
            )
            accept_cookies.click()
        except NoSuchElementException:
            pass

        products = get_products_from_page(driver=driver)
        write_files(product_name=product_name, products=products)


if __name__ == "__main__":
    get_all_products()
