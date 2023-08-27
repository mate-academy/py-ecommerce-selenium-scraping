import csv
import time
from dataclasses import dataclass, fields, astuple
from urllib.parse import urljoin
import bs4
import selenium
from selenium import webdriver
from selenium.webdriver.common.by import By
from tqdm import tqdm

BASE_URL = "https://webscraper.io/"

HOME_PAGE = urljoin(BASE_URL, "test-sites/e-commerce/more/")
COMPUTERS_PAGE = urljoin(BASE_URL, "test-sites/e-commerce/more/computers")
PHONES_PAGE = urljoin(BASE_URL, "test-sites/e-commerce/more/phones")
LAPTOPS_PAGE = urljoin(
    BASE_URL,
    "test-sites/e-commerce/more/computers/laptops"
)
TABLETS_PAGE = urljoin(
    BASE_URL,
    "test-sites/e-commerce/more/computers/tablets"
)
TOUCH_PAGE = urljoin(BASE_URL, "test-sites/e-commerce/more/phones/touch")

PAGES = [
    HOME_PAGE,
    COMPUTERS_PAGE,
    PHONES_PAGE,
    LAPTOPS_PAGE,
    TABLETS_PAGE,
    TOUCH_PAGE
]


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


class Parser:
    _instance = None

    def __new__(cls, *args, **kwargs) -> None:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, pages: list[str]) -> None:
        self.pages = pages
        self.chrome_options = webdriver.ChromeOptions()
        self.chrome_options.add_argument("--headless")
        self.driver = webdriver.Chrome(options=self.chrome_options)

    def accept_cookies(self) -> None:
        try:
            cookies_button = self.driver.find_element(
                by=By.CSS_SELECTOR,
                value="#cookieBanner > div.acceptContainer > a"
            )
            cookies_button.click()
        except selenium.common.exceptions.NoSuchElementException:
            pass

    def proceed_more_button(self) -> None:
        try:
            more_button = self.driver.find_element(
                by=By.CSS_SELECTOR,
                value="body > div.wrapper > div.container.test-site"
                      " > div > div.col-md-9 > a"
            )
        except selenium.common.exceptions.NoSuchElementException:
            more_button = None
        if more_button:
            while more_button.is_displayed():
                more_button.click()
                time.sleep(0.4)

    @staticmethod
    def write_to_csv(courses: list[Product], file_name: str) -> None:
        with open(
                file=file_name,
                mode="w",
                encoding="utf-8",
                newline=""
        ) as courses_file:
            writer = csv.writer(courses_file)
            writer.writerow([field.name for field in fields(Product)])
            writer.writerows([astuple(course) for course in courses])

    @staticmethod
    def parse_single_product(product_soup: bs4.element.Tag) -> Product:
        return Product(
            title=product_soup.select_one(".title")["title"],
            description=product_soup.select_one(
                ".description"
            ).text.replace(
                "\xa0",
                " "
            ),
            price=float(product_soup.select_one(
                ".price"
            ).text.replace(
                "$",
                ""
            )
            ),
            rating=int(len(product_soup.select(".ratings > p > span"))),
            num_of_reviews=int(
                product_soup.select_one(
                    ".ratings > p.pull-right"
                ).text.split()[0]
            ),
        )

    def parse_whole_page(self, page_soup: bs4.element.Tag) -> list[Product]:
        products = page_soup.select(".thumbnail")
        products_list = [
            self.parse_single_product(product) for product in tqdm(
                products,
                desc="Parsing products",
                colour="green",
                bar_format="{desc}: {percentage:3.0f}%|{bar}|"
                           " {n_fmt}/{total_fmt} [{elapsed}<{remaining}]",
            )
        ]
        return products_list

    def parse_all_pages(self) -> None:
        for page in self.pages:
            page_name = page.split("/")[-1]
            if page_name == "":
                page_name = "home"

            self.driver.get(page)
            self.accept_cookies()
            self.proceed_more_button()

            page_soup = bs4.BeautifulSoup(
                self.driver.page_source,
                "html.parser"
            )
            self.write_to_csv(
                self.parse_whole_page(page_soup),
                f"{page_name}.csv"
            )


def get_all_products() -> None:
    parser = Parser(PAGES)
    parser.parse_all_pages()


if __name__ == "__main__":
    get_all_products()
