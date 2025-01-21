import csv
from dataclasses import dataclass, fields, astuple
from urllib.parse import urljoin

from selenium.common import (
    ElementNotInteractableException,
    ElementClickInterceptedException
)
from selenium.webdriver import Chrome

from bs4 import (
    BeautifulSoup,
    Tag
)

import requests
from selenium.webdriver.common.by import By

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")
COMPUTERS_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/computers/")
PHONES_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/phones/")
LAPTOPS_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/computers/laptops")
TABLETS_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/computers/tablets")
TOUCHES_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/phones/touch")

LINKS_F_NAME = {
    HOME_URL: "home",
    COMPUTERS_URL: "computers",
    PHONES_URL: "phones",
    LAPTOPS_URL: "laptops",
    TABLETS_URL: "tablets",
    TOUCHES_URL: "touch",
}


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


PRODUCTS = [field.name for field in fields(Product)]


def create_page_link(base_url: str, next_page_url: str) -> str:
    return urljoin(base_url, next_page_url)


def get_soup_page_by_url(url: str) -> BeautifulSoup:
    res = requests.get(url, ).content
    soup = BeautifulSoup(res, "html.parser")
    return soup


def get_soup_page_by_html(html: str) -> BeautifulSoup:
    soup = BeautifulSoup(html, "html.parser")
    return soup


def get_cards(soup_page: BeautifulSoup) -> list[Tag]:
    cards = soup_page.select(".card")
    return cards


def is_more_button(soup_page: BeautifulSoup,) -> bool:
    more_button = soup_page.select(".ecomerce-items-scroll-more")
    if more_button:
        return True
    return False


def prepare_soup_page_with_more_button(page_link: str) -> BeautifulSoup:
    browser = Chrome()
    browser.get(page_link)
    btn_a_c = browser.find_elements(By.CSS_SELECTOR, ".acceptCookies")[0]
    more_button = browser.find_elements(
        By.CSS_SELECTOR,
        ".ecomerce-items-scroll-more"
    )[0]
    if btn_a_c:
        btn_a_c.click()
    while True:
        try:
            more_button.click()
        except ElementNotInteractableException:
            print("The more button is gone. Move ahead.")
            break
        except ElementClickInterceptedException:
            print("The more button is hidden. Move ahead")
            break
    page_html = browser.page_source
    browser.close()
    bs_page = get_soup_page_by_html(page_html)
    return bs_page


def get_product_link(soup_card: Tag) -> str:
    return soup_card.select(".title")[0].attrs["href"]


def reviews_from_row(row: str) -> int:
    row = str(row).replace("\t", "").replace("\n", "").split()[0]
    return int(row)


def clean_text(text: str) -> str:
    return text.replace("\xa0", " ").strip()


def parse_single_card(card: Tag) -> Product:
    title = clean_text(card.select(".title")[0]["title"])
    description = clean_text(str(card.select(".description")[0].contents[0]))
    price = str(card.select(".price")[0].contents[0]).replace("$", "")
    review = card.select(".review-count")[0]
    r_count = reviews_from_row(review.text)
    r_rating = len(card.select(".ws-icon-star"))
    product = Product(
        title=str(title),
        description=str(description),
        price=float(price),
        rating=r_rating,
        num_of_reviews=r_count,
    )
    return product


def write_to_csv(products: list[Product], name: str) -> None:
    with open(f"{name}.csv", "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(PRODUCTS)

        [
            writer.writerow(astuple(product))
            for product in products
        ]
        print(f"{name}.csv was successfully written.")


def get_all_products() -> None:
    for page_link in LINKS_F_NAME:
        bs_page = get_soup_page_by_url(page_link)
        more_button_on_page = is_more_button(bs_page)
        if more_button_on_page:
            bs_page = prepare_soup_page_with_more_button(page_link)
        cards = get_cards(bs_page)
        parsed_cards = [parse_single_card(card) for card in cards]
        f_name = LINKS_F_NAME[page_link]
        write_to_csv(parsed_cards, f_name)


if __name__ == "__main__":
    get_all_products()
