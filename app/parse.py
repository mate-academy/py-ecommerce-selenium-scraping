import csv

from dataclasses import dataclass, fields
from urllib.parse import urljoin
from bs4 import BeautifulSoup, Tag
from selenium import webdriver
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions
from tqdm import tqdm


BASE_URL = "https://webscraper.io/"
PAGES = {
    "home": "test-sites/e-commerce/more/",
    "computers": "test-sites/e-commerce/more/computers",
    "phones": "test-sites/e-commerce/more/phones",
    "laptops": "test-sites/e-commerce/more/computers/laptops",
    "tablets": "test-sites/e-commerce/more/computers/tablets",
    "touch": "test-sites/e-commerce/more/phones/touch",
}


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


PRODUCT_FIELDS = [field.name for field in fields(Product)]


def get_headless_driver() -> WebDriver:
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    driver = webdriver.Chrome(options=chrome_options)

    return driver


def cookies_button(driver: WebDriver) -> None:
    while True:
        try:
            accept_cookies = driver.find_element(
                By.CLASS_NAME, "acceptCookies"
            )
            accept_cookies.click()
        except Exception:
            break


def more_button_scroll(driver: WebDriver) -> None:
    while True:
        try:
            more_button = WebDriverWait(driver, 5).until(
                expected_conditions.element_to_be_clickable(
                    (By.CSS_SELECTOR, ".btn.ecomerce-items-scroll-more")
                )
            )
            more_button.click()
        except Exception:
            break


def parse_single_product(product_soup: Tag) -> Product:
    return Product(
        title=product_soup.select_one(".title")["title"],
        description=(product_soup.select_one(".description")
                     .text.replace("\xa0", " ")),
        price=float(product_soup.select_one(".price")
                    .text.replace("$", "")),
        rating=len(product_soup.select(".ws-icon")),
        num_of_reviews=int(product_soup.select_one(".review-count")
                           .text.split()[0]),
    )


def write_products_info(
        products_list: list[Product],
        output_csv_path: str
) -> None:
    with open(
            output_csv_path,
            "w",
            encoding="utf-8",
            newline=""
    ) as product_file:
        writer = csv.writer(product_file)
        writer.writerow(PRODUCT_FIELDS)
        for product in products_list:
            writer.writerow(
                [
                    product.title,
                    product.description,
                    product.price,
                    product.rating,
                    product.num_of_reviews,
                ]
            )


def get_all_products() -> None:
    driver = get_headless_driver()

    for name, link in tqdm(
            PAGES.items(),
            desc="Processing download",
            unit="page"
    ):
        page = urljoin(BASE_URL, link)
        driver.get(page)
        cookies_button(driver)
        more_button_scroll(driver)
        html_page = driver.page_source
        page_soup = BeautifulSoup(html_page, "html.parser")
        products_soup = page_soup.select(".card-body")
        products = [
            parse_single_product(product) for product in products_soup
        ]
        write_products_info(products, f"{name}.csv")

    driver.quit()


if __name__ == "__main__":
    get_all_products()
