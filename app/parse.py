import re
import csv
import requests
from dataclasses import dataclass
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import WebDriverWait


BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")
SIMPLE_PARSE_URLS = [
    {
        "url": HOME_URL,
        "file_name": "home.csv"
    },
    {
        "url": urljoin(HOME_URL, "computers"),
        "file_name": "computers.csv"
    },
    {
        "url": urljoin(HOME_URL, "phones"),
        "file_name": "phones.csv"
    },
]
SELENIUM_PARSE_URLS = [
    {
        "url": urljoin(HOME_URL, "computers/laptops"),
        "file_name": "laptops.csv"
    },
    {
        "url": urljoin(HOME_URL, "computers/tablets"),
        "file_name": "tablets.csv"
    },
    {
        "url": urljoin(HOME_URL, "phones/touch"),
        "file_name": "touch.csv"
    },
]


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


def parse_and_write_to_file(html: str, file_name: str) -> None:
    soup = BeautifulSoup(html, "html.parser")
    cards = soup.select(".thumbnail")

    products: list[Product] = []

    for card in cards:
        title_tag = card.select_one(".title")
        if title_tag:
            title = title_tag[
                "title"
            ] if title_tag and title_tag.has_attr("title") else title_tag.get_text(
                strip=True
            )

        description_tag = card.select_one(".description")
        raw_description = description_tag.get_text(
            strip=True
        ) if description_tag else ""
        description = raw_description.replace("\xa0", " ")

        price_str = card.select_one(".price").get_text(strip=True)
        price = float(price_str.replace("$", ""))

        # Правильний селектор для зірочок
        rating = len(card.select(".ws-icon-star"))

        # Надійний парсинг кількості відгуків
        reviews_tag = card.select_one(".ratings p.pull-right")
        if reviews_tag:
            reviews_text = reviews_tag.get_text(strip=True)
            match = re.search(r"\d+", reviews_text)
            num_of_reviews = int(match.group()) if match else 0
        else:
            num_of_reviews = 0

        products.append(Product(
            title=title,
            description=description,
            price=price,
            rating=rating,
            num_of_reviews=num_of_reviews
        ))

    with open(file_name, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "title",
            "description",
            "price",
            "rating",
            "num_of_reviews"
        ])
        for product in products:
            writer.writerow([
                product.title,
                product.description,
                product.price,
                product.rating,
                product.num_of_reviews
            ])


def parse_simple_page(url: str, file_name: str) -> None:
    response = requests.get(url)
    response.raise_for_status()
    html = response.text

    parse_and_write_to_file(html, file_name)


def parse_page_with_more_button(url: str, file_name: str) -> None:
    options = Options()
    options.add_argument("--headless")

    driver = webdriver.Firefox(options=options)
    driver.get(url)

    wait = WebDriverWait(driver, timeout=10)

    try:
        accept = driver.find_element(By.ID, "accept-cookie-notification")
        accept.click()
    except Exception:
        pass

    while True:
        try:
            more_button = driver.find_element(By.CLASS_NAME, "btn-primary")
            product_count_before = len(
                driver.find_elements(By.CLASS_NAME, "thumbnail")
            )

            driver.execute_script(
                "arguments[0].click();",
                more_button
            )

            wait.until(
                lambda d: len(
                    d.find_elements(
                        By.CLASS_NAME,
                        "thumbnail")
                ) > product_count_before
            )

        except Exception:
            break

    html = driver.page_source
    driver.quit()

    parse_and_write_to_file(html, file_name)


def get_all_products() -> None:
    for url_info in SIMPLE_PARSE_URLS:
        parse_simple_page(url_info["url"], url_info["file_name"])

    for url_info in SELENIUM_PARSE_URLS:
        parse_page_with_more_button(url_info["url"], url_info["file_name"])


if __name__ == "__main__":
    get_all_products()
