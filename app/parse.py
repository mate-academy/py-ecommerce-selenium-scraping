import csv
import time
from dataclasses import dataclass, fields, astuple
from urllib.parse import urljoin

from bs4 import Tag, BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


PRODUCT_FIELDS = [field.name for field in fields(Product)]


def accept_cookies(driver: webdriver) -> None:
    cookies = WebDriverWait(driver, 5).until(
        EC.element_to_be_clickable((By.CLASS_NAME, "acceptCookies"))
    )
    cookies.click()


def parse_single_product(soup: Tag) -> Product:
    rating_node = soup.select_one("p[data-rating]")
    rating = int(rating_node["data-rating"]) if rating_node else 0

    return Product(
        title=soup.select_one(".title")["title"],
        description=soup.select_one(".description").text,
        price=float(soup.select_one(".price").text.replace("$", "")),
        rating=rating,
        num_of_reviews=int(soup.select_one(".review-count").text.split()[0])
    )


def scrape_single_page(driver: webdriver) -> list[Product]:
    wait = WebDriverWait(driver, 5)
    while True:
        current_count = len(driver.find_elements(By.CLASS_NAME, "product-wrapper"))

        buttons = driver.find_elements(By.CLASS_NAME, "ecomerce-items-scroll-more")
        if not buttons or not buttons[0].is_displayed():
            break
        buttons[0].click()

        wait.until(lambda d: len(d.find_elements(By.CLASS_NAME, "product-wrapper")) > current_count)

    soup = BeautifulSoup(driver.page_source, "html.parser")
    products = soup.select(".product-wrapper")

    return [parse_single_product(product) for product in products]


def process_category(driver: webdriver, category_name: str) -> list[Product]:
    print(f"Scraping {category_name}")
    wait = WebDriverWait(driver, 5)

    sidebar = wait.until(EC.visibility_of_element_located((By.ID, "side-menu")))
    link = sidebar.find_element(By.LINK_TEXT, category_name)
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", link)

    time.sleep(0.2)

    link.click()

    wait.until(EC.presence_of_element_located((By.CLASS_NAME, "product-wrapper")))

    return scrape_single_page(driver)


def scrape_all_pages(driver: webdriver) -> dict[str, list[Product]]:
    all_products = {}
    categories = driver.find_elements(By.CSS_SELECTOR, "#side-menu > li > a")
    category_names = [category.text.strip() for category in categories]

    for category_name in category_names:
        all_products[category_name] = process_category(driver, category_name)

        sub_links = driver.find_elements(By.CSS_SELECTOR, ".nav-second-level > li > a")
        if sub_links:
            sub_names = [link.text.strip() for link in sub_links]

            for sub_name in sub_names:
                all_products[sub_name] = process_category(driver, sub_name)

    return all_products


def write_to_csv(all_products: dict[str, list[Product]]) -> None:
    for page_name, products in all_products.items():
        print(f"Writing to {page_name.lower()}.csv")
        with open(f"{page_name}.csv", "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(PRODUCT_FIELDS)
            writer.writerows([astuple(product) for product in products])


def get_all_products() -> None:
    driver = webdriver.Edge()
    driver.get(HOME_URL)
    time.sleep(0.2)

    accept_cookies(driver)

    all_products = scrape_all_pages(driver)
    write_to_csv(all_products)

    driver.close()


if __name__ == "__main__":
    get_all_products()
