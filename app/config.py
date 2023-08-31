from dataclasses import dataclass
from urllib.parse import urljoin


BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")
HTML_PARSER = "html.parser"
CLASS_SELECTS = ".swatches"
CLASS_PRODUCT = "thumbnail"
CLASS_BUTTON_COOKIES = "acceptCookies"
CLASS_URLS = ".sidebar-nav > ul > li > a"
CLASS_INNER_URLS = "ul.nav-second-level > li > a"
CLASS_MORE_BUTTON = "ecomerce-items-scroll-more"
CLASS_TITLE = "title"
CLASS_DESCRIPTION = "description"
CLASS_PRICE = "price"
CLASS_STAR_RATING = "ws-icon-star"
CLASS_REVIEW = "div.ratings > p.pull-right"
CHROME_OPTIONS = "--headless=new"
PRODUCT_FIELDS = ["title", "description", "price", "rating", "num_of_reviews"]


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int

    def __str__(self) -> str:
        return (f"title: {self.title}, \n"
                f" description: {self.description}, \n"
                f" price: {self.price}, \n"
                f" rating: {self.rating}, \n"
                f" reviews: {self.num_of_reviews}")
