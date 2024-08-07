from dataclasses import dataclass


BASE_URL = "https://webscraper.io/test-sites/e-commerce/more/"

URLS = {
    "HOME_PAGE_URL": f"{BASE_URL}",
    "COMPUTERS_PAGE_URL": f"{BASE_URL}computers",
    "LAPTOPS_PAGE_URL": f"{BASE_URL}computers/laptops",
    "TABLETS_PAGE_URL": f"{BASE_URL}computers/tablets",
    "PHONES_PAGE_URL": f"{BASE_URL}phones",
    "TOUCH_PAGE_URL": f"{BASE_URL}phones/touch"
}


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int
