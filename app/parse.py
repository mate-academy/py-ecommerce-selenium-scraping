import csv
from dataclasses import dataclass, astuple, fields
from urllib.parse import urljoin
from bs4 import BeautifulSoup, Tag
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium import webdriver


BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")

PRODUCT_PAGES = {
    "home": HOME_URL,
    "computers": urljoin(HOME_URL, "computers"),
    "laptops": urljoin(HOME_URL, "computers/laptops"),
    "tablets": urljoin(HOME_URL, "computers/tablets"),
    "phones": urljoin(HOME_URL, "phones"),
    "touch": urljoin(HOME_URL, "phones/touch"),
}


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


PRODUCT_FIELDS = [field.name for field in fields(Product)]


def parse_single_product(product_soup: Tag) -> Product:
    return Product(
        title=product_soup.select_one(".title")["title"],
        description=product_soup.select_one("p.description").text.replace(
            "\xa0", " "
        ),
        price=float(product_soup.select_one(".price").text[1:]),
        rating=len(product_soup.select("span.ws-icon-star")),
        num_of_reviews=int(
            product_soup.select_one(".review-count").text.split()[0]
        ),
    )


def get_all_products_from_page(url: str, driver: WebDriver) -> list[Product]:
    driver.get(url)

    try:
        more_button = driver.find_element(By.CLASS_NAME, "btn-primary")
    except Exception:
        more_button = None

    if more_button:
        while not more_button.get_property("style"):
            driver.execute_script("arguments[0].click();", more_button)

    soup = BeautifulSoup(driver.page_source, "html.parser")

    products_soup = soup.select(".thumbnail")
    result = [parse_single_product(product_soup) for product_soup in products_soup]

    return result

def write_products_to_csv(
        products: list[Product],
        csv_path: str
) -> None:
    with open(csv_path, "w", newline="", encoding="utf-8") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(PRODUCT_FIELDS)
        writer.writerows([astuple(product) for product in products])


def get_all_products() -> None:
    try:
        with webdriver.Chrome() as driver:
            for page_name, page_url in PRODUCT_PAGES.items():
                products = get_all_products_from_page(page_url, driver)
                write_products_to_csv(products, f"{page_name}.csv")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    get_all_products()
