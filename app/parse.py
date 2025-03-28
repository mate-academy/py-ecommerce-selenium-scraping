import csv
import json
from dataclasses import dataclass, fields
from time import sleep
from urllib.parse import urljoin

from bs4 import BeautifulSoup, Tag
from selenium import webdriver
from selenium.common import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions
from tqdm import tqdm

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")
COMPUTER_URL = urljoin(BASE_URL, "/test-sites/e-commerce/more/computers/")
LAPTOP_URL = urljoin(BASE_URL, "/test-sites/e-commerce/more/computers/laptops")
TABLET_URL = urljoin(BASE_URL, "/test-sites/e-commerce/more/computers/tablets")
PHONE_URL = urljoin(BASE_URL, "/test-sites/e-commerce/more/phones/")
TOUCH_URL = urljoin(BASE_URL, "/test-sites/e-commerce/more/phones/touch")

URL_AND_CSV_PATH = {
    "home": ["home.csv", HOME_URL],
    "computers": ["computers.csv", COMPUTER_URL],
    "laptops": ["laptops.csv", LAPTOP_URL],
    "tablets": ["tablets.csv", TABLET_URL],
    "phones": ["phones.csv", PHONE_URL],
    "touch": ["touch.csv", TOUCH_URL],
}

OPTIONS_WEBDRIVER = webdriver.ChromeOptions()
OPTIONS_WEBDRIVER.add_argument("--headless=new")


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int
    additional_info: dict


def get_element_or_false(
        by: By, value: str, elem: WebElement
) -> WebElement | bool:
    try:
        element = elem.find_element(by, value)
        return element
    except NoSuchElementException:
        return False


def click_banner_cookie(driver: WebElement) -> None:
    cookie_container = get_element_or_false(
        by=By.CLASS_NAME, value="acceptContainer", elem=driver
    )

    if cookie_container:
        button_cookie = cookie_container.find_element(By.TAG_NAME, "button")
        WebDriverWait(driver, 0.5).until(
            expected_conditions.element_to_be_clickable(button_cookie)
        )
        button_cookie.click()


def click_more_button(driver: WebElement) -> None:
    more = get_element_or_false(
        elem=driver, by=By.CLASS_NAME, value="ecomerce-items-scroll-more"
    )
    while more and more.is_displayed():
        more.click()
        sleep(0.1)


def get_hdd_price(elem: WebElement, driver: WebElement) -> dict[str, float]:
    hdd_price = {}

    buttons = elem.find_elements(By.TAG_NAME, "button")

    for button in buttons:
        if not button.get_property("disabled"):
            button.click()
            hdd = button.get_property("value")
            price = float(
                driver.find_element(
                    By.CLASS_NAME, "price"
                ).text.replace("$", "")
            )
            hdd_price[hdd] = price

    return hdd_price


def get_color_product(elem: WebElement) -> list[str]:
    colors = []

    items = elem.find_elements(By.CLASS_NAME, "dropdown-item")

    for item in items[1:]:
        colors.append(item.get_property("value"))

    return colors


def get_additional_info(product: Tag, driver: WebElement) -> dict:
    url = urljoin(BASE_URL, product.select_one(".title")["href"])
    additional_info = {}

    driver.get(url)
    click_banner_cookie(driver)
    product = driver.find_element(By.CLASS_NAME, "card-body")

    hdd_elem = get_element_or_false(
        elem=product,
        by=By.CLASS_NAME,
        value="swatches"
    )
    color_elem = get_element_or_false(
        elem=product,
        by=By.CLASS_NAME,
        value="dropdown"
    )

    if hdd_elem:
        hdd_price = get_hdd_price(hdd_elem, driver)
        additional_info["hdd"] = hdd_price

    if color_elem:
        colors = get_color_product(color_elem)
        additional_info["colors"] = colors

    return additional_info


def parse_product(product: Tag, driver: WebElement) -> Product:
    data = {
        "title": product.select_one(".title")["title"],
        "description": product.select_one(".description").text,
        "price": float(product.select_one(".price").text.replace("$", "")),
        "rating": product.select_one(".review-count").text.split()[0],
        "num_of_reviews": len(product.select(".ws-icon-star")),
        "additional_info": get_additional_info(product, driver)
    }
    return Product(**data)


def parse_page(page_url: str, name_process: str) -> list[Product]:
    with webdriver.Chrome(OPTIONS_WEBDRIVER) as driver:
        driver.get(page_url)
        click_banner_cookie(driver)
        click_more_button(driver)
        html = driver.page_source

        soup = BeautifulSoup(html, "html.parser")
        products_soup = soup.select(".card-body")

        products_list = []

        for product in tqdm(
                products_soup,
                desc=f"Progress: {name_process.title()}"
        ):
            products_list.append(parse_product(product, driver))

        return products_list


def save_product_csv(file_name: str, objects: list[Product]) -> None:
    with open(file_name, "w", encoding="UTF-8", newline="") as f:
        field_names = [field.name for field in fields(objects[0])]

        writer = csv.writer(f)
        writer.writerow(field_names)

        for obj in objects:
            row = [getattr(obj, field) for field in field_names]
            row[-1] = json.dumps(row[-1])
            writer.writerow(row)


def get_all_products() -> None:
    for name, value in URL_AND_CSV_PATH.items():
        url = value[1]
        file_name = value[0]
        products = parse_page(url, name)
        save_product_csv(file_name, products)


if __name__ == "__main__":
    get_all_products()
