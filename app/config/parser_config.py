from dataclasses import dataclass
from urllib.parse import urljoin

from selenium.webdriver.chrome.options import Options

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")
TOP_COMPUTERS_URL = urljoin(
    BASE_URL, "test-sites/e-commerce/more/computers"
)
TOP_PHONES_URL = urljoin(
    BASE_URL, "test-sites/e-commerce/more/phones"
)
PHONES_TOUCH_URL = urljoin(
    BASE_URL, "test-sites/e-commerce/more/phones/touch"
)
COMPUTERS_LAPTOPS_URL = urljoin(
    BASE_URL, "test-sites/e-commerce/more/computers/laptops"
)
COMPUTERS_TABLETS_URL = urljoin(
    BASE_URL, "test-sites/e-commerce/more/computers/tablets"
)

options = Options()
options.add_argument("--headless=new")


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int
