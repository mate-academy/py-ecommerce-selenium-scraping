import csv
from dataclasses import dataclass, astuple
import time
from typing import List, Dict
from urllib.parse import urljoin
from bs4 import Tag, BeautifulSoup
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int
    additional_info: Dict[str, float] | None


def handle_cookie_banner(driver):
    try:
        cookie_banner = driver.find_element(By.ID, "cookieBanner")
        if cookie_banner.is_displayed():
            try:
                accept_btn = cookie_banner.find_element(By.TAG_NAME, "button")
                accept_btn.click()
            except Exception:
                driver.execute_script("arguments[0].style.display = 'none';", cookie_banner)
    except Exception:
        pass


def get_linked_products(start_url: str) -> Dict[str, str]:
    options = Options()
    options.add_argument("--headless")
    driver = webdriver.Chrome(options=options)
    driver.get(start_url)
    handle_cookie_banner(driver)
    time.sleep(0.01)

    category_links = {}

    navi_box = driver.find_element(By.ID, "side-menu")
    categories = navi_box.find_elements(By.CSS_SELECTOR, "li.nav-item")

    for category in categories:
        subcategories = category.find_elements(By.CLASS_NAME, "category-link nav-link active")
        if subcategories:
            for sub in subcategories:
                try:
                    name = sub.find_element(By.CSS_SELECTOR, 'span[itemprop="name"]').text.strip()
                    href = sub.find_element(By.TAG_NAME, "a").get_attribute("href")
                    link = urljoin(BASE_URL, href)
                    category_links[name] = link
                except Exception:
                    continue
        else:
            try:
                name = category.find_element(By.CSS_SELECTOR, 'span[itemprop="name"]').text.strip()
                href = category.find_element(By.TAG_NAME, "a").get_attribute("href")
                link = urljoin(BASE_URL, href)
                category_links[name] = link
            except Exception:
                continue

    driver.quit()
    return category_links


def parse_additional_info(product: Tag) -> Dict[str, float]:
    abs_url = urljoin(BASE_URL, product.select_one(".title")["href"])
    options = Options()
    options.add_argument("--headless")
    driver = webdriver.Chrome(options=options)
    driver.get(abs_url)
    handle_cookie_banner(driver)
    time.sleep(0.03)

    while True:
        buttons = driver.find_elements(By.CLASS_NAME, "ecomerce-items-scroll-more")
        if not buttons:
            break
        try:
            buttons[0].click()
            time.sleep(0.01)
        except Exception:
            break

    prices = {}
    swatches = driver.find_elements(By.CLASS_NAME, "swatches")
    for swatch in swatches:
        buttons = swatch.find_elements(By.TAG_NAME, "button")
        for button in buttons:
            if not button.get_property("disabled"):
                button.click()
                time.sleep(0.1)
                price_text = driver.find_element(By.CLASS_NAME, "price").text.replace("$", "").strip()
                try:
                    prices[button.get_property("value")] = float(price_text)
                except ValueError:
                    continue

    driver.quit()
    return prices


def parse_single_product(product: Tag) -> Product:
    additional_info = parse_additional_info(product)
    title = product.select_one(".title").text.strip()
    description = product.select_one(".description").text.strip()
    price_text = product.select_one(".price").text.replace("$", "").strip()
    price = float(price_text)
    rating = int(product.select_one("p[data-rating]")["data-rating"])
    num_of_reviews_text = product.select_one(".review-count").text.strip()
    num_of_reviews = int(num_of_reviews_text.split()[0])
    return Product(
        title=title,
        description=description,
        price=price,
        rating=rating,
        num_of_reviews=num_of_reviews,
        additional_info=additional_info if additional_info else None
    )


def get_home_products(soup: BeautifulSoup) -> List[Product]:
    products = soup.select(".card-body")
    return [parse_single_product(product) for product in products]


def write_to_file(products: List[Product], category: str) -> None:
    with open(f"{category}.csv", "w", encoding="utf-8", newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Title", "Description", "Price", "Rating", "Number of Reviews", "Additional Info"])
        writer.writerows([astuple(product) for product in products])


if __name__ == "__main__":
    category_links = get_linked_products(HOME_URL)
    for category, link in category_links.items():
        print(f"Parsing category: {category}")
        response = requests.get(link)
        soup = BeautifulSoup(response.text, "html.parser")
        products = get_home_products(soup)
        write_to_file(products, category)
        print(f"Finished parsing {category} with {len(products)} products.")
