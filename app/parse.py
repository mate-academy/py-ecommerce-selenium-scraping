from selenium import webdriver
from app.product_parser import ProductParser
from app.constants import (
    HOME_URL,
    COMPUTERS_URL,
    LAPTOPS_URL,
    TABLETS_URL,
    PHONES_URL,
    TOUCH_URL,
    options
)


def get_all_products() -> None:
    with webdriver.Chrome(options=options) as driver:
        parser = ProductParser(driver)
        for category, url, file_name in [
            ("Home products", HOME_URL, "home.csv"),
            ("Computer products", COMPUTERS_URL, "computers.csv"),
            ("Laptop products", LAPTOPS_URL, "laptops.csv"),
            ("Tablet products", TABLETS_URL, "tablets.csv"),
            ("Phone products", PHONES_URL, "phones.csv"),
            ("Touch products", TOUCH_URL, "touch.csv"),
        ]:
            print(category)
            parser.parse_page(url, file_name)


if __name__ == "__main__":
    get_all_products()
