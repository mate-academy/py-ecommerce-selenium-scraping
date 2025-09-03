from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.ie.webdriver import WebDriver

from app.config import get_settings
from app.get_driver import set_driver
from app.models import PRODUCT_FIELDS
from app.parsers.page_parser import get_products_from
from app.services.cookies import accept_cookies
from app.utils.csv_writer import write_elements_to_csv
from app.utils.logger import logger

settings = get_settings()


def create_driver() -> WebDriver:
    options = Options()
    options.add_argument("--headless")
    driver = webdriver.Firefox(options=options)
    return driver


def get_all_products() -> None:
    driver = create_driver()
    with driver:
        set_driver(driver)
        driver.get(settings.HOME_URL)
        logger.debug(driver.current_url)
        accept_cookies()
        write_elements_to_csv(
            get_products_from(settings.HOME_URL),
            "home.csv",
            PRODUCT_FIELDS,
        )
        write_elements_to_csv(
            get_products_from(settings.COMPUTERS_URL),
            "computers.csv",
            PRODUCT_FIELDS,
        )
        write_elements_to_csv(
            get_products_from(settings.TABLETS_URL),
            "tablets.csv",
            PRODUCT_FIELDS,
        )
        write_elements_to_csv(
            get_products_from(settings.LAPTOPS_URL),
            "laptops.csv",
            PRODUCT_FIELDS,
        )
        write_elements_to_csv(
            get_products_from(settings.PHONES_URL),
            "phones.csv",
            PRODUCT_FIELDS,
        )
        write_elements_to_csv(
            get_products_from(settings.TOUCH_URL),
            "touch.csv",
            PRODUCT_FIELDS,
        )


if __name__ == "__main__":
    get_all_products()
