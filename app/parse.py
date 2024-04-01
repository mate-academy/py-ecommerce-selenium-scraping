import time
from selenium import webdriver

from .product import ProductParser, PRODUCT_FIELDS, Product
from .file_manager import CSVFileManager
from .settings import webscraper_page_urls
from .web_driver import WebDriverSingleton


def get_all_products() -> None:
    start = time.perf_counter()
    with webdriver.Chrome() as driver:

        driver.maximize_window()
        WebDriverSingleton(driver)

        for file_name, url in webscraper_page_urls.items():
            products: list[Product] = ProductParser(
                page_url=url
            ).get_all_products()

            file_manager = CSVFileManager(
                file_name=file_name, column_fields=PRODUCT_FIELDS
            )
            file_manager.write_in_csv_file(data=products)

    end = time.perf_counter()
    print(end - start)


if __name__ == "__main__":
    get_all_products()
