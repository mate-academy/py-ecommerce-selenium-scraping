import csv
import logging
import sys
import time
from dataclasses import dataclass, fields, astuple
from selenium import webdriver
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from urllib.parse import urljoin

from bs4 import BeautifulSoup, Tag


BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more")
COMPUTERS_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/computers")
LAPTOPS_URL = urljoin(
    BASE_URL,
    "test-sites/e-commerce/more/computers/laptops"
)
TABLETS_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/computers/tablets")
PHONES_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/phones")
TOUCH_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/phones/touch")

pages_list = {
    "home": HOME_URL,
    "computers": COMPUTERS_URL,
    "laptops": LAPTOPS_URL,
    "tablets": TABLETS_URL,
    "phones": PHONES_URL,
    "touch": TOUCH_URL,
}


# selenium headless mode options for hide browser window
options = Options()
options.add_argument("--headless=new")
options.add_argument("--window-size=1920,1080")

_driver: WebDriver | None = None


def get_driver() -> WebDriver:
    return _driver


def set_driver(new_driver: WebDriver) -> None:
    global _driver
    _driver = new_driver


@dataclass
class Product:
    """
    You can add additional_info to products by uncomment it here
    and in project below.
    """
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int
    # additional_info: dict | None


PRODUCT_FIELDS = [field.name for field in fields(Product)]

logging.basicConfig(
    level=logging.DEBUG,
    format="[%(levelname)8s]: %(message)s",
    handlers=[
        logging.FileHandler("parser.log"),
        logging.StreamHandler(sys.stdout),
    ]
)


def parse_additional_info(product_soup: Tag) -> tuple[dict[str, float], int]:
    absolute_url = urljoin(BASE_URL, product_soup.select_one(".title")["href"])
    driver = get_driver()
    driver.get(absolute_url)
    prices = {}
    soup = BeautifulSoup(driver.page_source, "html.parser")
    stars = soup.select("span.ws-icon-star")

    if soup.select_one("div.swatches"):
        swatches = driver.find_element(By.CLASS_NAME, "swatches")
        buttons = swatches.find_elements(By.TAG_NAME, "button")

        for button in buttons:
            if not button.get_property("disabled"):
                button.click()
                prices[button.get_property("value")] = float(
                    driver.find_element(
                        By.CLASS_NAME, "price"
                    ).text.replace("$", "")
                )

    return prices, len(stars)


def parse_single_product(product: Tag) -> Product:
    hdd_prices, detailed_rating = parse_additional_info(product)
    stars = product.select("span.ws-icon-star")
    rating = len(stars)
    ## on laptops list page ratings of all products is 5
    ## but in details it is not, so if you want to choose rating from details
    ## just uncomment code below
    # if rating != detailed_rating:
    #     rating = detailed_rating

    return Product(
        title=product.select_one(".title")["title"],
        description=product.select_one(".description").text,
        price=float(product.select_one(".price").text.replace("$", "")),
        rating=rating,
        num_of_reviews=int(
            product.select_one(".review-count").text.split()[0]
        ),
        ## for add additional_info to products uncomment lines below
        # additional_info={"hdd_price": hdd_prices} if hdd_prices else {}
        # additional_info = {"hdd_price": hdd_prices}
    )


def get_single_page_products(page_soup: Tag) -> list[Product]:
    products = page_soup.select(".card-body")
    return [parse_single_product(product) for product in products]


def get_all_products() -> None:
    logging.info("Start parsing laptops")
    btn_accept_cookies_selector = ".acceptCookies"
    btn_more_selector = \
        "a.btn.btn-lg.btn-block.btn-primary.ecomerce-items-scroll-more"

    for filename, page_url in pages_list.items():
        driver = get_driver()
        driver.get(page_url)

        # press button for accept cookies if exist
        try:
            button_accept_cookies = WebDriverWait(driver, 3).until(
                ec.element_to_be_clickable(
                    (By.CSS_SELECTOR, btn_accept_cookies_selector,)
                )
            )
            button_accept_cookies.click()
            time.sleep(1)
        except (TimeoutException, NoSuchElementException):
            logging.info("There is no button for accept cookies — continue")

        # press button "more" (load more products) if exist
        while True:
            try:
                button_more = WebDriverWait(driver, 3).until(
                    ec.element_to_be_clickable(
                        (By.CSS_SELECTOR, btn_more_selector,)
                    )
                )
                button_more.click()
                time.sleep(1)
            except (TimeoutException, NoSuchElementException):
                logging.info("There is no more button 'More'")
                break

        # parse all products
        page_html = driver.page_source
        soup = BeautifulSoup(page_html, "html.parser")
        all_products = get_single_page_products(soup)

        # write products to csv
        write_products_to_csv(all_products, filename)


def write_products_to_csv(products: list[Product], filename: str) -> None:
    with open(f"{filename}.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(PRODUCT_FIELDS)
        writer.writerows([astuple(product) for product in products])


def main() -> None:
    with webdriver.Chrome(options=options) as driver:
        set_driver(driver)
        get_all_products()


if __name__ == "__main__":
    main()
