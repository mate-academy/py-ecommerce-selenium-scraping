from selenium import webdriver

from app.scrappers.computer_scrapper import (
    get_top_computer_page_products,
    get_laptop_products,
    get_tablets_products
)
from app.scrappers.home_page_scrapper import get_home_page_products
from app.config.parser_config import options
from app.scrappers.phone_scrapper import (
    get_top_phone_page_products,
    get_phone_touch_with_pagination_products
)


def get_all_products() -> None:
    driver = webdriver.Chrome(options=options)
    try:
        get_home_page_products(driver)
        get_top_computer_page_products(driver)
        get_top_phone_page_products(driver)
        get_phone_touch_with_pagination_products(driver)
        get_laptop_products(driver)
        get_tablets_products(driver)
    finally:
        driver.quit()


if __name__ == "__main__":
    get_all_products()
