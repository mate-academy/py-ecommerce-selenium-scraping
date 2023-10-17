import csv
import re
import time
from dataclasses import astuple

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from tqdm import tqdm

from app.models import Product, PRODUCT_FIELDS
from app.settings import lst_urls


def get_name_csv_file(url: str) -> str:
    parts = url.split("/")
    last_word = parts[-1] if parts[-1] else parts[-2]
    if last_word == "more":
        last_word = "home"
    return last_word


def get_products(url: str, driver: webdriver) -> list[Product]:
    driver.get(url)
    if driver.find_elements(
            By.CLASS_NAME,
            "btn.btn-lg.btn-block.btn-primary.ecomerce-items-scroll-more"
    ):
        more = driver.find_element(
            By.CLASS_NAME,
            "btn.btn-lg.btn-block.btn-primary.ecomerce-items-scroll-more"
        )
        counter = len(driver.find_elements(By.CLASS_NAME, "card-body"))

        while True:
            driver.execute_script("arguments[0].click();", more)
            time.sleep(2)

            counter_new = len(driver.find_elements(By.CLASS_NAME, "card-body"))
            if counter_new == counter:
                break

            counter = counter_new

    cards = driver.find_elements(By.CLASS_NAME, "card-body")
    products = []
    for card in tqdm(cards, desc="Scraping Products"):
        title = card.find_element(
            By.CLASS_NAME, "title"
        ).get_attribute("title")
        description = card.find_element(
            By.CLASS_NAME, "card-text.description"
        ).text
        rating = len(card.find_elements(
            By.CLASS_NAME, "ws-icon.ws-icon-star"
        ))
        num_of_reviews = int(
            re.sub(r"[^0-9]", "", card.find_element(
                By.CLASS_NAME, "ratings"
            ).text))
        price = float(card.find_element(
            By.CLASS_NAME, "float-end.price.pull-right"
        ).text.replace("$", ""))

        products.append(
            Product(
                title=title,
                description=description,
                price=price,
                rating=rating,
                num_of_reviews=num_of_reviews,
            )
        )
    return products


def write_products_to_csv(
        products: list[Product],
        output_csv_path: str
) -> None:
    with open(output_csv_path, "w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(PRODUCT_FIELDS)
        writer.writerows(
            [astuple(quote) for quote in tqdm(products, desc="Writing to CSV")]
        )


def get_all_products() -> None:
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    driver = webdriver.Chrome(options=chrome_options)

    for url in lst_urls:
        products = get_products(url, driver)
        write_products_to_csv(
            products=products, output_csv_path=f"{get_name_csv_file(url)}.csv"
        )

    driver.quit()


if __name__ == "__main__":
    get_all_products()
