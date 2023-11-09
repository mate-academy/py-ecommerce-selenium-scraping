import unicodedata

from selenium import webdriver
from selenium.webdriver.common.by import By

from app.product import Product
from app.csv_files.csv_writer import write_products_to_file
from app.pages.more_btn_handler import handle_btn


def normalize_description(description: str) -> str:
    return unicodedata.normalize("NFKD", description).replace("\xa0", " ")


def rating_parser(driver: webdriver, more_btn: bool) -> (webdriver, int):
    if more_btn:
        ratings_div = driver.find_element(By.CLASS_NAME, "ratings")
        span_elements = ratings_div.find_elements(By.TAG_NAME, "span")
        return driver, len(span_elements)
    else:
        ratings_element = driver.find_element(By.CLASS_NAME, "ratings")
        rating_element = ratings_element.find_element(
            By.XPATH, "//p[@data-rating]"
        )
        data_rating = rating_element.get_attribute("data-rating")
        return driver, int(data_rating)


def page_parser(
    url: str, driver: webdriver, file_name: str, more_btn: bool = False
) -> list[Product]:
    products_list = []
    if more_btn:
        driver = handle_btn(driver, url)
    else:
        driver.get(url)

    products = driver.find_elements(By.CLASS_NAME, "card-body")
    for product in products:
        title_element = product.find_element(By.CLASS_NAME, "title")
        title = title_element.get_attribute("title")

        description_element = product.find_element(
            By.CLASS_NAME, "description"
        )
        description = description_element.get_attribute("textContent")
        description = normalize_description(description)

        price_element = product.find_element(By.CLASS_NAME, "price")
        price = price_element.get_attribute("textContent")
        price = float(price[1:])

        driver, data_rating = rating_parser(driver, more_btn)

        num_of_reviews_element = product.find_element(
            By.CLASS_NAME, "review-count"
        )
        num_of_reviews = num_of_reviews_element.text
        num_of_reviews = int(num_of_reviews.split(" ")[0])

        product = Product(
            title=title,
            description=description,
            price=price,
            rating=data_rating,
            num_of_reviews=num_of_reviews,
        )
        products_list.append(product)

    write_products_to_file(products_list, file_name)
    return products_list
