from bs4 import BeautifulSoup, Tag
from selenium import webdriver

from app.constants import LAPTOPS_URL
from app.models import Product
from app.utils import close_cookies_banner, click_show_more_until_gone


def parse_single_laptops_product(product: Tag) -> Product:
    return Product(
        title=product.select_one(".title")["title"],
        description=product.select_one(
            ".description"
        ).text.replace("\xa0", " "),
        price=float(product.select_one(".price").text.replace("$", "")),
        rating=len(product.select(".ratings .ws-icon-star")),
        num_of_reviews=int(product.select_one(".review-count").text.split()[0])
    )


def get_laptops_products() -> list[Product]:
    with webdriver.Chrome() as driver:
        driver.get(LAPTOPS_URL)
        close_cookies_banner(driver)
        click_show_more_until_gone(driver)
        page_source = driver.page_source

    soup = BeautifulSoup(page_source, "html.parser")
    products = soup.select(".card-body")
    return [parse_single_laptops_product(product) for product in products]
