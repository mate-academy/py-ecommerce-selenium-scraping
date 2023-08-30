from dataclasses import dataclass
from urllib.parse import urljoin


BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")
HTML_PARSER = "html.parser"
CLASS_SELECTS = ".swatches"
CLASS_PRODUCT = "thumbnail"
# CLASS_CONTAINER_COOKIES = ".cookieBanner"
CLASS_BUTTON_COOKIES = "acceptCookies"
CLASS_INNER_URLS = "ul.nav-second-level > li > a"
CLASS_MORE_BUTTON = "ecomerce-items-scroll-more"
CLASS_TITLE = "title"
CLASS_DESCRIPTION = "description"
CLASS_PRICE = "price"
CHROME_OPTIONS = "--headless=new"


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int

    def __str__(self):
        return f"title {self.title}, \n descr {self.description}, \n pri {self.price}, \n rat {self.rating}, \n num {self.num_of_reviews}"
