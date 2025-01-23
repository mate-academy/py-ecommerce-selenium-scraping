import csv
import dataclasses
import time
from dataclasses import dataclass
import requests
from bs4 import BeautifulSoup, Tag
from selenium.common import NoSuchElementException
from selenium.webdriver import ActionChains

from selenium import webdriver
from selenium.webdriver.common.by import By
from tqdm import tqdm

page_to_scrape = [
    {
        "file_name": "phones.csv",
        "url": "https://webscraper.io/test-sites/e-commerce/more/phones",
    },
    {
        "file_name": "home.csv",
        "url": "https://webscraper.io/test-sites/e-commerce/more",
    },
    {
        "file_name": "computers.csv",
        "url": "https://webscraper.io/test-sites/e-commerce/more/computers",
    },
]

page_with_pagination = [
    {
        "file_name": "laptops.csv",
        "url": "https://webscraper.io/test-sites/"
               "e-commerce/more/computers/laptops",
    },
    {
        "file_name": "tablets.csv",
        "url": "https://webscraper.io/test-sites/"
               "e-commerce/more/computers/tablets",
    },
    {
        "file_name": "touch.csv",
        "url": "https://webscraper.io/test-sites/"
               "e-commerce/more/phones/touch",
    },
]


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


def bulk_write_csv_file(filename: str, products: list[dict]) -> None:
    with open(filename, "w", newline="", encoding="utf-8") as file:
        fieldnames = [field.name for field in dataclasses.fields(Product)]
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(products)


class ParseTopItems:

    @classmethod
    def get_tag(cls,
                code_to_parse: Tag,
                type_tag: str,
                name_tag: str | dict
                ) -> Tag:
        parse_tag = code_to_parse.find(type_tag, name_tag)
        if parse_tag is None:
            raise ValueError(f"{type_tag}: "
                             f"{name_tag} not found from {code_to_parse}")
        return parse_tag

    def get_title(self, code_to_parse: Tag) -> str:
        title_tag = self.get_tag(code_to_parse, "a", "title")
        return title_tag.get("title")

    def get_description(self, code_to_parse: Tag) -> str:
        description_tag = self.get_tag(code_to_parse, "p", "description")
        return description_tag.text

    def get_price(self, code_to_parse: Tag) -> float:
        price_tag = self.get_tag(
            code_to_parse, "h4", "price float-end card-title pull-right"
        )
        return float(price_tag.text.replace("$", ""))

    def get_num_of_reviews(self, code_to_parse: Tag) -> int:
        num_reviews_tag = self.get_tag(
            code_to_parse, "p", "review-count float-end"
        )
        num = num_reviews_tag.text.split(" ")
        return int(num[0])

    def get_rating(self, code_to_parse: Tag) -> int:
        rating_tag = self.get_tag(code_to_parse, "p", {"data-rating": True})
        return int(rating_tag.get("data-rating"))

    def parse_three_products_page(self, page_url: str) -> list[dict]:
        response = requests.get(page_url).content
        soup = BeautifulSoup(response, "html.parser")
        page = soup.find_all("div", "col-md-4 col-xl-4 col-lg-4")

        list_products = [
            {
                "title": self.get_title(elem),
                "description": self.get_description(elem),
                "price": self.get_price(elem),
                "rating": self.get_rating(elem),
                "num_of_reviews": self.get_num_of_reviews(elem),
            }
            for elem in page
        ]
        return list_products


class ParsePagePagination:
    def __init__(self) -> None:
        options = webdriver.ChromeOptions()
        options.add_argument("--headless=new")
        self.driver = webdriver.Chrome(options=options)

    def parse_items(self, url: str) -> list[dict]:
        self.driver.get(url)
        # Click to cookies button if existed.
        try:
            cookie = self.driver.find_element(By.ID, "cookieBanner")
            button = cookie.find_element(By.CLASS_NAME, "acceptCookies")
            button.click()
        except NoSuchElementException:
            pass

        while True:
            try:
                button_more = self.driver.find_element(
                    By.CLASS_NAME,
                    "btn.btn-lg.btn-block.btn-primary."
                    "ecomerce-items-scroll-more",
                )
                time.sleep(0.5)

                style = button_more.get_attribute("style")
                if "display: none;" in style:
                    break
                actions = ActionChains(self.driver)
                actions.move_to_element(button_more).perform()
                button_more.click()

            except NoSuchElementException:
                break

        elems = self.driver.find_elements(
            By.CLASS_NAME,
            "col-md-4.col-xl-4.col-lg-4"
        )

        products = [
            {
                "title": product.find_element(
                    By.CLASS_NAME,
                    "title")
                .get_attribute(
                    "title"
                ),
                "description": product.find_element(
                    By.CLASS_NAME, "card-text.description"
                ).text,
                "price": float(
                    product.find_element(
                        By.CLASS_NAME, "price.float-end.pull-right"
                    ).text.replace("$", "")
                ),
                "rating": len(
                    product.find_elements(
                        By.CLASS_NAME,
                        "ws-icon.ws-icon-star"
                    )
                ),
                "num_of_reviews": int(
                    product.find_element(
                        By.CLASS_NAME, "review-count.float-end.pull-right"
                    ).text.split(" ")[0]
                ),
            }
            for product in elems
        ]
        return products

    def close_driver(self) -> None:
        self.driver.close()


def get_all_products() -> None:
    # parse with tqdm progress meter
    for site_conf in tqdm(page_to_scrape,
                          desc="Parsing static pages",
                          unit="page"):
        parse_top_products = ParseTopItems()
        products = parse_top_products.parse_three_products_page(
            site_conf.get("url")
        )
        bulk_write_csv_file(site_conf.get("file_name"), products)

    parse_items_pagination = ParsePagePagination()

    # parse with tqdm progress meter
    for site_conf in tqdm(
        page_with_pagination, desc="Parsing paginated pages", unit="page"
    ):
        products = parse_items_pagination.parse_items(site_conf.get("url"))
        bulk_write_csv_file(site_conf.get("file_name"), products)

    parse_items_pagination.close_driver()


if __name__ == "__main__":
    get_all_products()
