import csv
from dataclasses import dataclass
from urllib.parse import urljoin

import selenium.common.exceptions
from bs4 import BeautifulSoup
import requests
from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


def get_soup(url):
    content = requests.get(url).content
    soup = BeautifulSoup(content, "html.parser")
    return soup


def get_data_from_soup(soup: BeautifulSoup, url: str):
    if soup.select_one(".btn"):
        driver = webdriver.Chrome()
        driver.get(url)
        actions = ActionChains(driver)
        try:
            button = driver.find_element(By.CSS_SELECTOR,
                                         "a.btn.btn-lg.btn-block.btn-primary.ecomerce-items-scroll-more")
            style = button.get_attribute("style")

            while not style:
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                actions.move_to_element(button).click().perform()
        except selenium.common.exceptions.NoSuchElementException:
            driver.close()
        except selenium.common.exceptions.JavascriptException:
            print("last_page")

        all_products = driver.find_elements(By.CLASS_NAME, "card")
        return [
            {
                "title": product.find_element(By.CLASS_NAME, "title").get_attribute("title"),
                "description": product.find_element(By.CLASS_NAME, "description").text,
                "price": float(product.find_element(By.CLASS_NAME, "price").text.replace("$", "")),
                "rating": len(product.find_elements(By.CLASS_NAME, "ws-icon")),
                "num_of_reviews": int(product.find_element(By.CLASS_NAME, "review-count").text.strip().replace("reviews", "")),
            }
            for product in all_products
        ]

    all_products = soup.select(".card")
    return [
        {
            "title": product.select_one("a.title")["title"],
            "description": product.select_one(".description").text,
            "price": float(product.select_one(".price").text.replace("$", "")),
            "rating": int(product.select_one("p[data-rating]")["data-rating"]),
            "num_of_reviews": int(product.select_one("p.review-count").text.strip().replace("reviews", "")),
        }
        for product in all_products
    ]


def create_product_objects(all_products_data: list[dict]) -> list[Product]:
    return [
        Product(
            title=product["title"],
            description=product["description"],
            price=product["price"],
            rating=product["rating"],
            num_of_reviews=product["num_of_reviews"]
        )
        for product in all_products_data
    ]


def save_as_csv_file(file_name: str, all_products_data: list[dict]) -> None:
    with open(file_name, "w", newline="") as file:
        fieldnames = ["title", "description", "price", "rating", "num_of_reviews"]
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_products_data)


def get_all_products() -> None:
    list_of_urls = [
        urljoin(BASE_URL, "test-sites/e-commerce/more"),
        urljoin(BASE_URL, "test-sites/e-commerce/more/computers"),
        urljoin(BASE_URL, "test-sites/e-commerce/more/computers/laptops"),
        urljoin(BASE_URL, "test-sites/e-commerce/more/computers/tablets"),
        urljoin(BASE_URL, "test-sites/e-commerce/more/phones"),
        urljoin(BASE_URL, "test-sites/e-commerce/more/phones/touch")
    ]
    for url in list_of_urls:
        csv_file_name = "home.csv" if url.split("/")[-1] == "more" else url.split("/")[-1] + ".csv"
        soup = get_soup(url)
        all_products_data = get_data_from_soup(soup, url=url)
        save_as_csv_file(file_name=csv_file_name, all_products_data=all_products_data)
        create_product_objects(all_products_data)


if __name__ == "__main__":
    get_all_products()
