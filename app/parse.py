import csv
import logging
import sys
import time
from dataclasses import dataclass, fields, asdict
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup, Tag
from selenium import webdriver
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("parser.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


def setup(url: str) -> WebDriver:
    driver = webdriver.Chrome()
    driver.get(url)
    return driver


def teardown(driver: WebDriver) -> None:
    driver.quit()


def make_safe_request(url: str) -> str:
    try:
        response = requests.get(url=url)
        if response.status_code == 200:
            return response.text
    except Exception as e:
        logging.warning(e)


def get_product_price(product: Tag) -> float:
    price_container = product.select_one(".price")
    if not price_container:
        return 0.0

    # Try nested [itemprop='price'] first
    price_tag = price_container.select_one("[itemprop='price']")
    if price_tag:
        price_text = price_tag.text.strip()
    else:
        price_text = price_container.text.strip()

    price_text = price_text.replace("$", "")
    try:
        return float(price_text)
    except ValueError:
        return 0.0


def get_product_ratings(product: Tag) -> dict:
    ratings_container = product.select_one(".ratings")
    star_count = 0

    rating_tag = ratings_container.select_one("p[data-rating]")
    if rating_tag is None:
        try:
            stars = product.select(".ws-icon.ws-icon-star")
            star_count = len(stars)
        except Exception as e:
            logging.info(f"Cannot calculate stars on card!: {e}")
    else:
        star_count = rating_tag["data-rating"]

    num_of_reviews = ratings_container.select_one(
        "[itemprop='reviewCount']"
    ).text.strip()
    return {"rating": int(star_count), "num_of_reviews": int(num_of_reviews)}


def get_product_title(product: Tag) -> str:
    title_container = product.select_one(".title")
    return title_container["title"]


def clean_text(text: str) -> str:
    return text.replace("\xa0", " ").strip()


def create_product_obj(card: Tag) -> Product:
    ratings = get_product_ratings(product=card)
    return Product(
        title=get_product_title(product=card),
        description=clean_text(card.select_one(".description ").text),
        price=get_product_price(product=card),
        rating=ratings["rating"],
        num_of_reviews=ratings["num_of_reviews"]
    )


def load_full_page(driver: WebDriver) -> None:
    while True:
        try:
            # Try to locate the "More" button
            more_button = driver.find_element(By.CSS_SELECTOR, ".btn-primary")
            if not more_button.is_displayed():
                logging.warning("More button is hidden. Done.")
                break

            # Click the button
            more_button.click()
            time.sleep(1)

        except Exception as e:
            logging.warning(f"More button not found or click failed:{e}")
            break


def is_more_btn(driver: WebDriver) -> bool:
    try:
        btn_more = driver.find_element(
            By.CSS_SELECTOR,
            ".ecomerce-items-scroll-more"
        )
        if btn_more.is_displayed():
            return True
        else:
            return False
    except Exception as e:
        logging.warning(f"Btn 'More' not found: {e}")


def accept_cookies(driver: WebDriver) -> None:
    try:
        WebDriverWait(driver, 5)
        cookie_btn = driver.find_element(By.CLASS_NAME, "acceptCookies")
        if cookie_btn.is_displayed():
            cookie_btn.click()
        logging.info("Accepted Cookies for website!")
    except Exception as e:
        logging.warning(f"Btn 'acceptCookies' not found: {e}")


def get_html_via_selenium(url: str) -> BeautifulSoup:
    driver = setup(url=url)
    accept_cookies(driver=driver)
    try:
        if is_more_btn(driver=driver):
            load_full_page(driver)

        return BeautifulSoup(driver.page_source, "html.parser")
    except Exception as e:
        logging.warning(f"Page source not found:{e}")
    finally:
        logging.info(f"{driver.name} close!")
        teardown(driver)


def get_soup_from_page(url: str) -> BeautifulSoup | None:
    soup = BeautifulSoup(make_safe_request(url), "html.parser")

    if soup.body and "No products found!" in soup.get_text():
        logging.warning(f"No products found on page!{url}")
        return None

    # Load via Selenium if not found cards on response
    elif not soup.select_one(".card-body"):
        soup = get_html_via_selenium(url=url)

    return soup


def get_products_from_single_page(soup: BeautifulSoup) -> list[Product] | None:
    products = []
    cards = soup.select(".card-body")
    if cards:
        for card in cards:
            products.append(create_product_obj(card=card))
    else:
        logging.info("Cards not found!")
    return products


def save_data_to_csv(name: str, products: list[Product]) -> None:
    with open(
            f"{name}.csv",
            mode="w",
            newline="",
            encoding="utf-8"
    ) as csvfile:
        fieldnames = [field.name for field in fields(Product)]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        if products is None:
            return
        for product in products:
            writer.writerow(asdict(product))  # Serialize and write


def get_products_from_page(home_url: str, path: str = None) -> None:
    url = urljoin(home_url, path)  # Make url
    logging.info(f"Working on {url}")

    soup = get_soup_from_page(url=url)

    products = get_products_from_single_page(soup=soup)

    # Save to csv file by name of path
    if path is None:
        path = "home"
    name_of_csv_file = path.split("/")[-1]
    save_data_to_csv(name=name_of_csv_file, products=products)


def get_all_products() -> None:
    get_products_from_page(home_url=HOME_URL)  # home page (3 random products);
    get_products_from_page(home_url=HOME_URL, path="computers")
    get_products_from_page(home_url=HOME_URL, path="computers/laptops")
    get_products_from_page(home_url=HOME_URL, path="computers/tablets")
    get_products_from_page(home_url=HOME_URL, path="phones")
    get_products_from_page(home_url=HOME_URL, path="phones/touch")


if __name__ == "__main__":
    get_all_products()
