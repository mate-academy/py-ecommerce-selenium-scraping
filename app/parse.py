import csv
import time
from dataclasses import dataclass, astuple
from urllib.parse import urljoin

from bs4 import Tag, BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")

_driver: WebDriver | None = None


def get_driver() -> WebDriver:
    return _driver


def set_driver(new_driver: WebDriver) -> None:
    global _driver
    _driver = new_driver


@dataclass
class Product:
    title: str
    description: str
    price: str
    rating: str
    num_of_reviews: str
    additional_info: str = ""

    def __init__(
        self,
        title: str,
        description: str,
        price: str,
        rating: str,
        num_of_reviews: str,
        additional_info: dict | None = None
    ) -> None:
        self.title = title
        self.description = description
        self.price = price
        self.rating = rating
        self.num_of_reviews = num_of_reviews
        if (
            additional_info is None
            or additional_info == "{}"
            or additional_info == ""
        ):
            self.additional_info = ""
        else:
            self.additional_info = additional_info


def accept_cookies() -> None:
    driver = get_driver()
    try:
        cookie_button = driver.find_element(
            By.CLASS_NAME, "acceptCookies"
        )
        cookie_button.click()
        time.sleep(0.3)
    except Exception:
        pass


def parse_hdd_info(product_soup: Tag) -> dict[str, float]:
    absolute_url = urljoin(BASE_URL, product_soup.select_one(".title")["href"])
    driver = get_driver()
    driver.get(absolute_url)
    time.sleep(0.5)

    try:
        swatches = driver.find_element(By.CLASS_NAME, "swatches")
        buttons = swatches.find_elements(By.TAG_NAME, "button")
    except Exception:
        return {}

    prices = {}
    for button in buttons:
        if not button.get_attribute("disabled"):
            driver.execute_script("arguments[0].click();", button)
            time.sleep(0.2)
            price = float(
                driver
                .find_element(By.CLASS_NAME, "price")
                .text.replace("$", "")
            )
            prices[button.get_property("value")] = round(price, 2)
    return prices


def parse_colors(product_soup: Tag) -> list[str]:
    absolute_url = urljoin(BASE_URL, product_soup.select_one(".title")["href"])
    driver = get_driver()
    driver.get(absolute_url)
    time.sleep(0.5)

    try:
        select_element = driver.find_element(
            By.CSS_SELECTOR, ".dropdown select"
        )
        dropdown = Select(select_element)
        return [
            option.text for option in dropdown.options
            if option.get_attribute("value")
        ]
    except Exception:
        return []


def parse_single_product(product: Tag, current_url: str) -> Product:
    additional_info = {}
    if "phones" in current_url:
        colors = parse_colors(product)
        if colors:
            additional_info["colors"] = colors
    else:
        hdd_prices = parse_hdd_info(product)
        if hdd_prices:
            additional_info["hdd_prices"] = hdd_prices

    return Product(
        title=product.select_one(".title")["title"],
        description=product.select_one(".description").text.strip(),
        price=str(
            round(float(
                product.select_one(".price").text.strip().replace("$", "")), 2)
        ),
        rating=str(len(
            product.select_one(".ratings").select(".ws-icon-star")
        )),
        num_of_reviews=str(int(product.select_one(".review-count span").text)),
        additional_info=str(additional_info) if additional_info else "{}",
    )


def scrape_page_products(link: str) -> list[Product]:
    driver = get_driver()
    driver.get(link)

    while True:
        try:
            more_button = driver.find_element(
                By.CLASS_NAME, "ecomerce-items-scroll-more"
            )
            if not more_button.is_displayed():
                break
            driver.execute_script(
                "arguments[0].scrollIntoView({block: 'center'});", more_button
            )
            time.sleep(0.5)
            driver.execute_script("arguments[0].click();", more_button)
            time.sleep(2)
        except Exception:
            break

    soup = BeautifulSoup(driver.page_source, "html.parser")
    products_list = soup.select(".product-wrapper")
    return [parse_single_product(product, link) for product in products_list]


def write_products_to_csv(
    output_csv_path: str,
    products: list[Product]
) -> None:
    with open(output_csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "title",
            "description",
            "price",
            "rating",
            "num_of_reviews",
            "additional_info",
        ])
        writer.writerows([astuple(prod) for prod in products])


def get_all_products(link: str = None) -> list[Product]:
    sites_to_scrape = {
        "https://webscraper.io/test-sites/e-commerce/more":
            "home.csv",
        "https://webscraper.io/test-sites/e-commerce/more/computers":
            "computers.csv",
        "https://webscraper.io/test-sites/e-commerce/more/computers/laptops":
            "laptops.csv",
        "https://webscraper.io/test-sites/e-commerce/more/computers/tablets":
            "tablets.csv",
        "https://webscraper.io/test-sites/e-commerce/more/phones":
            "phones.csv",
        "https://webscraper.io/test-sites/e-commerce/more/phones/touch":
            "touch.csv",
    }

    if link is None:
        driver = webdriver.Chrome()
        set_driver(driver)

        driver.get(HOME_URL)
        accept_cookies()

        try:
            for url, output_csv_path in sites_to_scrape.items():
                products = scrape_page_products(url)
                write_products_to_csv(output_csv_path, products)
        finally:
            driver.quit()
        return []

    return scrape_page_products(link)


def main() -> None:
    get_all_products()


if __name__ == "__main__":
    main()
