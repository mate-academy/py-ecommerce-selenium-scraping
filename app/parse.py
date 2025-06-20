import csv

from dataclasses import dataclass
from urllib.parse import urljoin
from selenium import webdriver
from selenium.common import (
    ElementNotInteractableException,
    ElementClickInterceptedException,
)
from selenium.webdriver.common.by import By

BASE_URL = "https://webscraper.io/"

HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")

driver = webdriver.Chrome()


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


def get_all_item_with_pagination() -> None:
    try:
        button = driver.find_element(
            By.CSS_SELECTOR,
            "a.ecomerce-items-scroll-more"
        )
        while button.is_displayed() and button.is_enabled():
            driver.execute_script("arguments[0].click();", button)
    except ElementNotInteractableException:
        print("It`s already full content to scrape")
    except ElementClickInterceptedException:
        print("It`s already full content to scrape")


def get_all_items_from_page(
        link: str,
        pagination: bool = False
) -> list[Product]:
    """

    :param link: link to the page to scrape

    :param pagination: put True if more button present on page

    :return: list of Product items include HDD versions

    """

    driver.get(link)
    if pagination:
        get_all_item_with_pagination()

    items_on_page = driver.find_elements(By.CSS_SELECTOR, "div.card-body")
    items = []

    for i in range(len(items_on_page)):
        ratings_container = driver.find_elements(
            By.CSS_SELECTOR,
            "div.ratings"
        )[i]
        rating_elements = ratings_container.find_elements(
            By.CSS_SELECTOR,
            "span.ws-icon.ws-icon-star"
        )
        rating = len(rating_elements)
        num_of_reviews_container = driver.find_elements(
            By.CSS_SELECTOR,
            "p.review-count"
        )[i]
        num_of_reviews = num_of_reviews_container.find_element(
            By.CSS_SELECTOR,
            "span[itemprop='reviewCount']"
        ).text
        detail_link = driver.find_elements(By.CSS_SELECTOR, "a.title")[i]
        driver.execute_script("arguments[0].click();", detail_link)
        title = driver.find_element(By.CSS_SELECTOR, "h4.title").text
        description = driver.find_element(
            By.CSS_SELECTOR,
            "p.description"
        ).text
        price = float(driver.find_element(
            By.CSS_SELECTOR,
            "span[itemprop='price']"
        ).text.replace("$", ""))

        items.append(
            Product(
                title=title,
                description=description,
                num_of_reviews=int(num_of_reviews),
                rating=rating,
                price=price
            )
        )
        driver.back()

    return items


def write_items_to_csv(items: list[Product], output_csv_path: str) -> None:
    """

    Writes a list of Quote objects to a CSV file.

    """

    if not items:
        print(
            "No items to write to CSV. "
            "The CSV file will not be created or "
            "will be empty if it already exists."
        )
        return

    fieldnames = ["title", "description", "price", "rating", "num_of_reviews"]

    try:

        with open(
                output_csv_path,
                "w",
                newline="",
                encoding="utf-8"
        ) as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            writer.writeheader()
            for item in items:
                writer.writerow(
                    {
                        "title": item.title,
                        "description": item.description,
                        "price": item.price,
                        "rating": item.rating,
                        "num_of_reviews": item.num_of_reviews,
                    }
                )

            print(f"Successfully wrote "
                  f"{len(items)} quotes to {output_csv_path}")

    except IOError as e:
        print(f"Error writing to CSV file {output_csv_path}: {e}")

    except Exception as e:
        print(f"An unexpected error occurred while writing CSV: {e}")


def get_all_products() -> None:
    write_items_to_csv(get_all_items_from_page(HOME_URL), "home.csv")
    write_items_to_csv(
        get_all_items_from_page(
            f"{HOME_URL}computers"),
        "computers.csv")
    write_items_to_csv(
        get_all_items_from_page(
            f"{HOME_URL}computers/laptops",
            True),
        "laptops.csv"
    )
    write_items_to_csv(
        get_all_items_from_page(
            f"{HOME_URL}computers/tablets",
            True),
        "tablets.csv"
    )
    write_items_to_csv(
        get_all_items_from_page(
            f"{HOME_URL}phones"),
        "phones.csv"
    )
    write_items_to_csv(
        get_all_items_from_page(
            f"{HOME_URL}phones/touch",
            True),
        "touch.csv"
    )


if __name__ == "__main__":
    get_all_products()
    driver.close()
