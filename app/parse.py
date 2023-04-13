import csv
import unicodedata
from dataclasses import dataclass, astuple
from urllib.parse import urljoin

from bs4 import Tag, BeautifulSoup
from selenium import webdriver
from selenium.common import NoSuchElementException
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")
COMPUTERS_URL = urljoin(HOME_URL, "computers")
PHONES_URL = urljoin(HOME_URL, "phones")


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


def get_one_product(product_tag: Tag) -> Product:
    return Product(
        title=product_tag.select_one(".title")["title"],
        description=unicodedata.normalize(
            "NFKD", product_tag.select_one(".description").text
        ),
        price=float(product_tag.select_one(".price").text.replace("$", "")),
        rating=len(product_tag.select("div.ratings p span.glyphicon")),
        num_of_reviews=int(
            product_tag.select("div.ratings p")[0].text.split()[0]
        )
    )


def parse_one_page(page_html: str) -> tuple[list[Product], str]:
    soup = BeautifulSoup(page_html, "html.parser")
    product_tags = soup.select(".thumbnail")
    title = soup.select_one("link[rel='canonical']")["href"].split("/")[-1]

    if not title:
        title = "home"

    return (
        [get_one_product(product_tag) for product_tag in product_tags],
        title
    )


def get_whole_page(driver: webdriver.Chrome, url: str) -> str:
    driver.get(url)
    cookie_banner = driver.find_elements(By.ID, "cookieBanner")

    if cookie_banner and cookie_banner[0].is_displayed():
        cookie_accept = driver.find_element(By.CLASS_NAME, "acceptCookies")
        cookie_accept.click()

    try:
        more = driver.find_element(By.CLASS_NAME, "ecomerce-items-scroll-more")
    except NoSuchElementException:
        more = None

    if more and more.is_displayed():
        while more.is_displayed() and more.is_enabled():
            action = ActionChains(driver)
            action.move_to_element(more).click().perform()

    return driver.page_source


def write_pages_products_to_csv(products: list[Product], title: str) -> None:
    fields = ("title", "description", "price", "rating", "num_of_reviews")
    with open(
            f"{title}.csv", "w", newline="", encoding="utf-8"
    ) as result_file:
        csv_writer = csv.writer(result_file)
        csv_writer.writerow(fields)
        csv_writer.writerows([astuple(product) for product in products])


def get_all_products() -> None:
    urls = [
        HOME_URL,
        COMPUTERS_URL,
        PHONES_URL,
        PHONES_URL + "/touch",
        COMPUTERS_URL + "/laptops",
        COMPUTERS_URL + "/tablets"
    ]
    with webdriver.Chrome() as driver:
        for url in urls:
            page_source = get_whole_page(driver=driver, url=url)
            products, title = parse_one_page(page_source)
            write_pages_products_to_csv(products=products, title=title)


if __name__ == "__main__":
    get_all_products()
