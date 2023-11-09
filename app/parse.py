from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from urllib.parse import urljoin

from app.pages.page_parser import page_parser

chrome_options = Options()
chrome_options.add_argument('--headless')

driver = webdriver.Chrome(options=chrome_options)

BASE_URL = "https://webscraper.io/"

HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")
COMPUTERS_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/computers")
PHONES_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/phones")

LAPTOPS_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/computers/laptops")
TABLETS_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/computers/tablets")
TOUCH_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/phones/touch")


def get_all_products() -> None:
    products = []
    received_products = (
        page_parser(HOME_URL, driver, "home.csv"),
        page_parser(COMPUTERS_URL, driver, "computers.csv"),
        page_parser(PHONES_URL, driver, "phones.csv"),
        page_parser(LAPTOPS_URL, driver, "laptops.csv", more_btn=True),
        page_parser(TABLETS_URL, driver, "tablets.csv", more_btn=True),
        page_parser(TOUCH_URL, driver, "touch.csv", more_btn=True),
    )

    for received_product in received_products:
        products.extend(received_product)


if __name__ == "__main__":
    get_all_products()
    driver.close()
