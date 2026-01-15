from app.scraper.scraper import Scraper
from urllib.parse import urljoin
from selenium import webdriver
from selenium.webdriver.firefox.options import Options

from app.model.product import Product
from app.csv_export.csv_exporter import write_items_to_csv

options = Options()
options.add_argument("-headless")

BASE_URL = "https://webscraper.io/"

HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")
COMPUTERS_URL = urljoin(HOME_URL, "computers/")
LAPTOPS_URL = urljoin(COMPUTERS_URL, "laptops")
TABLETS_URL = urljoin(COMPUTERS_URL, "tablets")
PHONES_URL = urljoin(HOME_URL, "phones/")
TOUCH_URL = urljoin(PHONES_URL, "touch")


def get_all_products() -> None:

    with webdriver.Firefox(options=options) as web_driver:
        urls = {
            "home.csv": HOME_URL,
            "computers.csv": COMPUTERS_URL,
            "laptops.csv": LAPTOPS_URL,
            "tablets.csv": TABLETS_URL,
            "phones.csv": PHONES_URL,
            "touch.csv": TOUCH_URL,
        }
        scraper = Scraper(web_driver, HOME_URL)

        for path, url in urls.items():
            products_list: list[dict] = scraper.get_products_from_root_url(url)
            products = [Product(**product) for product in products_list]
            write_items_to_csv(products, path)


if __name__ == "__main__":
    get_all_products()
