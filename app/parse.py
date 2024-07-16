import csv
from dataclasses import dataclass
from urllib.parse import urljoin

from selenium import webdriver
from selenium.webdriver.common.by import By
import requests
from bs4 import BeautifulSoup


BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int
    additional_info: dict


def parse_hdd_block_prices(product_soup: BeautifulSoup) -> dict[str, float]:
    detailed_url = urljoin(HOME_URL, product_soup.select_one(".title")["href"])
    driver = webdriver.Chrome()
    driver.get(detailed_url)
    swatches = driver.find_element(By.CLASS_NAME, "swatches")
    buttons = swatches.find_elements(By.TAG_NAME, "button")

    prices = {}

    for button in buttons:
        if not button.get_property("disabled"):
            button.click()
            prices[button.get_property("value")] = float(driver.find_element(
                By.CLASS_NAME,
                "price"
            ).text.replace("$", ""))

    driver.close()

    return prices


def parse_product(product: BeautifulSoup) -> Product:
    hdd_prices = parse_hdd_block_prices(product)
    return Product(
        title=product.select_one(".title")["title"],
        description=product.select_one(".description").text,
        price=float(product.select_one(".price").text.replace("$", "")),
        rating=int(product.select_one("p[data-rating]")["data-rating"]),
        num_of_reviews=int(
            product.select_one(".review-count").text.split()[0]
        ),
        additional_info={"hdd_prices": hdd_prices},
    )


def scrape_page(url: str, category: str) -> None:
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    product_soup = soup.select(".thumbnail")
    products = [parse_product(product) for product in product_soup]
    save_to_csv(products, f"{category}.csv")


def save_to_csv(products: list, filename: str) -> None:
    with open(filename, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow([
            "title",
            "description",
            "price",
            "rating",
            "num_of_reviews",
            "additional_info"
        ])
        for product in products:
            writer.writerow([
                product.title,
                product.description,
                product.price,
                product.rating,
                product.num_of_reviews,
                product.additional_info
            ])


def get_all_products() -> None:
    pages_info = {
        "home": "test-sites/e-commerce/more/",
        "computers": "test-sites/e-commerce/more/computers",
        "laptops": "test-sites/e-commerce/more/computers/laptops",
        "tablets": "test-sites/e-commerce/more/computers/tablets",
        "phones": "test-sites/e-commerce/more/phones",
        "touch": "test-sites/e-commerce/more/phones/touch"
    }

    for category, path in pages_info.items():
        url = urljoin(BASE_URL, path)
        scrape_page(url, category)


if __name__ == "__main__":
    get_all_products()
