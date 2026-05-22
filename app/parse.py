import csv

from dataclasses import dataclass, fields, astuple
from urllib.parse import urljoin
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.webdriver import WebDriver as ChromeWebDriver
from selenium.webdriver.remote.webelement import WebElement

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")


class WebDriver:
    __instance = None
    __driver = None

    def __new__(cls, *args, **kwargs) -> "WebDriver":
        if cls.__instance is None:
            cls.__instance = super().__new__(cls)
        return cls.__instance

    @property
    def object(self) -> ChromeWebDriver:
        if self.__driver is None:
            self.__driver = webdriver.Chrome()
        return self.__driver

    def close(self) -> None:
        if self.__driver:
            self.__driver.quit()


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


def parse_single_product(product_body: WebElement) -> Product:
    title = product_body.find_element(By.CSS_SELECTOR, "a.title").get_attribute("title")
    description = product_body.find_element(By.CSS_SELECTOR, "p.description").text

    price: list = product_body.find_elements(By.CSS_SELECTOR, 'span[itemprop="price"]')
    if not price:  # search sub product price
        price = float(product_body.find_element(By.CSS_SELECTOR, "h4.price").text[1:])
    else:
        price = float(price[0].text[1:])

    rating = product_body.find_elements(By.CSS_SELECTOR, "p[data-rating]")
    if not rating:  # search sub product rating
        rating = len(product_body.find_elements(By.CSS_SELECTOR, "span.ws-icon"))
    else:
        rating = int(rating[0].get_attribute("data-rating"))
    num_of_reviews = int(
        product_body.find_element(By.CSS_SELECTOR, 'span[itemprop="reviewCount"]').text
    )

    return Product(
        title=title,
        description=description,
        price=price,
        rating=rating,
        num_of_reviews=num_of_reviews,
    )


def parse_all_products(web_driver: ChromeWebDriver) -> list[Product]:
    return [
        parse_single_product(product)
        for product in web_driver.find_elements(By.CSS_SELECTOR, "div.card-body")
    ]


def write_csv(result_dict: dict[str, list[Product]]) -> None:
    for csv_file_name, products in result_dict.items():
        with open(
            f"{csv_file_name}.csv", "w", newline="", encoding="utf-8"
        ) as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(field.name for field in fields(Product))
            writer.writerows(astuple(product) for product in products)


def get_all_products() -> None:
    driver = WebDriver()

    try:
        scrap_result = {}

        web_driver = driver.object
        web_driver.get(HOME_URL)

        home_products = parse_all_products(web_driver=web_driver)
        scrap_result["home"] = home_products

        other_urls = [
            urljoin(BASE_URL, element.get_attribute("href"))
            for element in web_driver.find_elements(By.CSS_SELECTOR, "a.category-link")
        ]
        for url in other_urls:
            web_driver.get(url)
            products = parse_all_products(web_driver=web_driver)

            page_name = url.rsplit("/", 1)[-1]
            scrap_result[page_name] = products

            subcategories = [
                urljoin(BASE_URL, element.get_attribute("href"))
                for element in web_driver.find_elements(
                    By.CSS_SELECTOR, "a.subcategory-link"
                )
            ]
            for sub_url in subcategories:
                web_driver.get(sub_url)

                sub_page_name = sub_url.rsplit("/", 1)[-1]
                while True:
                    more_button = web_driver.find_elements(
                        By.CSS_SELECTOR, "a.ecomerce-items-scroll-more"
                    )
                    if more_button and more_button[0].get_attribute("style"):
                        break
                    web_driver.execute_script("arguments[0].click();", more_button[0])

                sub_products = parse_all_products(web_driver=web_driver)
                scrap_result[sub_page_name] = sub_products
        write_csv(result_dict=scrap_result)

    finally:
        driver.close()


if __name__ == "__main__":
    get_all_products()
