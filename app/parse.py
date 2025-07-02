import csv
from time import sleep

from dataclasses import dataclass, fields
from urllib.parse import urljoin

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


PRODUCT_ROWS = [field.name for field in fields(Product)]


def get_result_dict(
        count: int,
        items: list[WebElement],
        title_class_name: str = "title",
        price_class_name: str = "price",
        description_class_name: str = "description",
        rating_class_name: str = "ratings",
        stars_class_name: str = "ws-icon-star",
        review_count_class_name: str = "review-count"
) -> list[Product]:
    result_dict = []
    for index, item in enumerate(items[:count]):
        title = item.find_element(
            By.CLASS_NAME,
            title_class_name
        ).get_attribute("title")
        description = item.find_element(
            By.CLASS_NAME,
            description_class_name
        ).text
        price = float(item.find_element(
            By.CLASS_NAME,
            price_class_name
        ).text.replace("$", ""))
        rating = item.find_element(By.CLASS_NAME, rating_class_name)
        rating_stars = len(rating.find_elements(
            By.CLASS_NAME,
            stars_class_name)
        )
        num_of_reviews = int(rating.find_element(
            By.CLASS_NAME,
            review_count_class_name
        ).text.split(" ")[0])

        result_dict.append(Product(
            title=title,
            description=description,
            price=price,
            rating=rating_stars,
            num_of_reviews=num_of_reviews)
        )

    return result_dict


def get_product(
        count: int,
        url: str,
        class_name: str,
) -> list[Product]:
    driver = webdriver.Chrome()
    driver.get(url)
    items = driver.find_elements(By.CLASS_NAME, class_name)

    result_dict = get_result_dict(
        count=count,
        items=items,
    )

    return result_dict


def get_product_with_button(
        url: str,
        class_name: str,
        count: int = None,
        button_name: str = None,
) -> list[Product]:
    driver = webdriver.Chrome()
    driver.get(url)
    cookies_btn = driver.find_element(By.CLASS_NAME, "acceptCookies")
    cookies_btn.click()

    button_element = driver.find_element(By.CLASS_NAME, button_name)

    while "More" in button_element.text:
        button_element.click()
        sleep(0.5)

    items = driver.find_elements(By.CLASS_NAME, class_name)

    items_result = get_result_dict(count=count, items=items)
    print(items_result)

    return items_result


def csv_writer(filename: str, data_to_write: list[Product]) -> None:
    with open(filename, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(PRODUCT_ROWS)

        for product in data_to_write:
            writer.writerow(
                [
                    product.title,
                    product.description,
                    product.price,
                    product.rating,
                    product.num_of_reviews
                ]
            )


def get_all_products() -> None:

    homes = get_product(
        count=3,
        url=HOME_URL,
        class_name="product-wrapper"
    )
    computers = get_product(count=3, url=(urljoin(
        BASE_URL,
        "test-sites/e-commerce/more/computers")
    ), class_name="product-wrapper")
    phones = get_product(count=3, url=(urljoin(
        BASE_URL,
        "test-sites/e-commerce/more/phones")
    ), class_name="product-wrapper")
    touches = get_product_with_button(
        count=9,
        url=(urljoin(
            BASE_URL,
            "test-sites/e-commerce/more/phones/touch")
        ),
        class_name="product-wrapper",
        button_name="btn-primary",
    )
    tablets = get_product_with_button(
        count=21,
        url=(urljoin(
            BASE_URL,
            "test-sites/e-commerce/more/computers/tablets")
        ),
        class_name="product-wrapper",
        button_name="btn-primary"
    )
    laptops = get_product_with_button(
        count=117,
        url=(urljoin(
            BASE_URL,
            "test-sites/e-commerce/more/computers/laptops")
        ),
        button_name="btn-primary",
        class_name="product-wrapper"
    )

    csv_writer("home.csv", homes)
    csv_writer("computers.csv", computers)
    csv_writer("phones.csv", phones)
    csv_writer("touch.csv", touches)
    csv_writer("tablets.csv", tablets)
    csv_writer("laptops.csv", laptops)

    print(laptops)
    print(phones)
    print(computers)


if __name__ == "__main__":
    get_all_products()
