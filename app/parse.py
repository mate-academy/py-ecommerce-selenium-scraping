from dataclasses import dataclass
from urllib.parse import urljoin
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import csv


BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int  # Changed here to be consistent with the dataclass


def setup_driver() -> webdriver.Chrome:
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver


def get_all_products() -> None:
    driver = setup_driver()
    driver.get(HOME_URL)

    product_cards = driver.find_elements("css selector", ".thumbnail")

    with open("products.csv", mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow([
            "title", "description", "price", "rating", "num_of_reviews"
        ])

        for card in product_cards:
            title_element = card.find_element("css selector", ".title")
            title = title_element.get_attribute(
                "title"
            ) or title_element.text.strip()

            description = card.find_element(
                "css selector", ".description"
            ).text
            price = float(
                card.find_element(
                    "css selector", ".price"
                ).text.replace("$", "")
            )
            rating = len(
                card.find_elements(
                    "css selector",
                    ".ratings .rating span.glyphicon-star"
                )
            )

            try:
                num_of_reviews = int(
                    card.find_element(
                        "css selector", ".ratings > p.pull-right"
                    ).text.split()[0]
                )
            except Exception:
                num_of_reviews = 0

            writer.writerow([
                title, description, price, rating, num_of_reviews
            ])

    driver.quit()


if __name__ == "__main__":
    get_all_products()
