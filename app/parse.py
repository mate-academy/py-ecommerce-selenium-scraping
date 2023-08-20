import csv
import asyncio
from dataclasses import dataclass, fields, astuple
from urllib.parse import urljoin

from selenium import webdriver
from selenium.common import NoSuchElementException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")
WINDOW_SIZE = "1920,1080"


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int
    additional_info: dict


PRODUCT_FIELDS = [field.name for field in fields(Product)]


def write_products_to_csv(products: list[Product], csv_file: str) -> None:
    with open(csv_file, "w", encoding="utf-8", newline="") as output_csv_file:
        writer = csv.writer(output_csv_file)
        writer.writerow(PRODUCT_FIELDS)
        writer.writerows([astuple(product) for product in products])


def get_driver() -> webdriver:
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--window-size=%s" % WINDOW_SIZE)
    driver = webdriver.Chrome(options=chrome_options)

    return driver


async def parse_hdd_block_prices(
    product_element: WebElement,
) -> dict[str, float]:
    detailed_url = urljoin(
        BASE_URL,
        product_element.find_element(By.CLASS_NAME, "title").get_attribute(
            "href"
        ),
    )
    driver = get_driver()
    driver.get(detailed_url)
    try:
        swatches = driver.find_element(By.CLASS_NAME, "swatches")
        buttons = swatches.find_elements(By.TAG_NAME, "button")

        prices = {}

        for button in buttons:
            if not button.get_property("disabled"):
                button.click()
                prices[button.get_property("value")] = float(
                    driver.find_element(By.CLASS_NAME, "price").text.replace(
                        "$", ""
                    )
                )
        driver.close()
        return prices
    except NoSuchElementException:
        pass


async def parse_single_product(product_element: WebElement) -> Product:
    title = product_element.find_element(By.CLASS_NAME, "title").get_attribute(
        "title"
    )
    description = product_element.find_element(
        By.CLASS_NAME, "description"
    ).text
    price = float(
        product_element.find_element(By.CLASS_NAME, "price").text.replace(
            "$", ""
        )
    )

    rating_elements = product_element.find_elements(
        By.CSS_SELECTOR, "p span.ws-icon-star"
    )
    rating = len(rating_elements)

    num_of_reviews = int(
        product_element.find_element(
            By.CSS_SELECTOR, ".ratings > p.pull-right"
        ).text.split()[0]
    )

    hdd_prices = await parse_hdd_block_prices(product_element)

    additional_info = {"hdd_prices": hdd_prices} if hdd_prices else None

    return Product(
        title=title,
        description=description,
        price=price,
        rating=rating,
        num_of_reviews=num_of_reviews,
        additional_info=additional_info,
    )


async def get_random_products(url: str, csv_file_path: str) -> None:
    driver = get_driver()
    driver.get(url)

    all_home_products = []

    while True:
        try:
            more_button = driver.find_element(By.CLASS_NAME, "btn-primary")
            if more_button.is_displayed():
                more_button.click()
            else:
                break
        except NoSuchElementException:
            break

    products = driver.find_elements(By.CSS_SELECTOR, ".thumbnail")

    for product in products:
        all_home_products.append(await parse_single_product(product))

    write_products_to_csv(products=all_home_products, csv_file=csv_file_path)
    driver.close()


async def get_all_products() -> None:
    await asyncio.gather(
        get_random_products(HOME_URL, "home.csv"),
        get_random_products(urljoin(HOME_URL, "phones"), "phones.csv"),
        get_random_products(urljoin(HOME_URL, "computers"), "computers.csv"),
        get_random_products(urljoin(HOME_URL, "phones/touch"), "touch.csv"),
        get_random_products(
            urljoin(HOME_URL, "computers/tablets"), "tablets.csv"
        ),
        get_random_products(
            urljoin(HOME_URL, "computers/laptops"), "laptops.csv"
        ),
    )


if __name__ == "__main__":
    asyncio.run(get_all_products())
