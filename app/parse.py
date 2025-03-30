import csv
import json
from time import sleep
from types import TracebackType
from urllib.parse import urljoin
from typing import Optional, Type
from dataclasses import dataclass, fields

from tqdm import tqdm
from bs4.element import Tag
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support import expected_conditions as ec


BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")
COMPUTER_URL = urljoin(BASE_URL, "/test-sites/e-commerce/more/computers/")
LAPTOP_URL = urljoin(BASE_URL, "/test-sites/e-commerce/more/computers/laptops")
TABLET_URL = urljoin(BASE_URL, "/test-sites/e-commerce/more/computers/tablets")
PHONE_URL = urljoin(BASE_URL, "/test-sites/e-commerce/more/phones/")
TOUCH_URL = urljoin(BASE_URL, "/test-sites/e-commerce/more/phones/touch")


URL_AND_CSV_PATH_MAPPING = {
    "home": ["home.csv", HOME_URL],
    "computers": ["computers.csv", COMPUTER_URL],
    "laptops": ["laptops.csv", LAPTOP_URL],
    "tablets": ["tablets.csv", TABLET_URL],
    "phones": ["phones.csv", PHONE_URL],
    "touch": ["touch.csv", TOUCH_URL],
}


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int
    additional_info: dict


class FirefoxWebDriverContextManager:
    def __init__(self, headless: bool = True) -> None:
        self.headless: bool = headless
        self.driver: Optional[webdriver.Firefox] = None

    def __enter__(self) -> webdriver.Firefox:
        options = webdriver.FirefoxOptions()
        if self.headless:
            options.add_argument("-headless")
        self.driver = webdriver.Firefox(options=options)
        return self.driver

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_value: Optional[BaseException],
        traceback: Optional[TracebackType]
    ) -> None:
        self.driver.quit()


def get_element(
        by: By, value: str, context: WebDriver | WebElement
) -> Optional[WebElement]:
    try:
        element = context.find_element(by, value)
        return element
    except NoSuchElementException:
        return None


def click_banner_cookie(driver: WebDriver) -> None:
    cookie_container = get_element(
        by=By.CLASS_NAME, value="acceptContainer", context=driver
    )

    if cookie_container:
        button_cookie = cookie_container.find_element(By.TAG_NAME, "button")
        WebDriverWait(driver, 0.5).until(
            ec.element_to_be_clickable(button_cookie)
        )
        button_cookie.click()


def click_more_button(driver: WebDriver) -> None:
    more = get_element(
        context=driver, by=By.CLASS_NAME, value="ecomerce-items-scroll-more"
    )
    while more and more.is_displayed():
        more.click()
        sleep(0.1)


def get_hdd_price(elem: WebElement, driver: WebDriver) -> dict[str, float]:
    hdd_price = {}

    buttons = elem.find_elements(By.TAG_NAME, "button")

    for button in buttons:
        if not button.get_property("disabled"):
            button.click()
            hdd = button.get_property("value")
            price = round(
                float(
                    driver.find_element(
                        By.CLASS_NAME, "price"
                    ).text.replace("$", "")
                ),
                2
            )
            hdd_price[hdd] = price

    return hdd_price


def get_product_color(elem: WebElement) -> list[str]:
    colors = []
    items = elem.find_elements(By.CLASS_NAME, "dropdown-item")

    for item in items[1:]:
        colors.append(item.get_property("value"))

    return colors


def get_additional_info(product: Tag, driver: WebDriver) -> dict:
    url = urljoin(BASE_URL, product.select_one(".title")["href"])
    additional_info = {}

    driver.get(url)

    WebDriverWait(driver, 10).until(
        ec.presence_of_element_located((By.CLASS_NAME, "card-body"))
    )

    click_banner_cookie(driver)

    product_body = driver.find_element(By.CLASS_NAME, "card-body")

    hdd_elem = get_element(
        by=By.CLASS_NAME,
        value="swatches",
        context=product_body
    )
    if hdd_elem:
        hdd_price = get_hdd_price(hdd_elem, driver)
        additional_info["hdd"] = hdd_price

    color_elem = get_element(
        by=By.CLASS_NAME,
        value="dropdown",
        context=product_body
    )
    if color_elem:
        colors = get_product_color(color_elem)
        additional_info["colors"] = colors

    return additional_info


def parse_product(product: Tag, driver: WebDriver) -> Product:
    data = {
        "title": product.select_one(".title")["title"],
        "description": product.select_one(".description").text,
        "price": round(
            float(product.select_one(".price").text.replace("$", "")),
            2
        ),
        "rating": int(product.select_one(".review-count").text.split()[0]),
        "num_of_reviews": len(product.select(".ws-icon-star")),
        "additional_info": get_additional_info(product, driver)
    }
    return Product(**data)


def parse_page(
    driver: webdriver.Firefox,
    page_url: str,
    name_process: str
) -> list[Product]:

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


def save_product_to_csv(file_name: str, objects: list[Product]) -> None:
    with open(file_name, "w", encoding="UTF-8", newline="") as f:
        field_names = [field.name for field in fields(objects[0])]
        writer = csv.writer(f)
        writer.writerow(field_names)

        for obj in objects:
            row = [getattr(obj, field) for field in field_names]
            row[-1] = json.dumps(row[-1])
            writer.writerow(row)


def get_all_products(headless: bool = True) -> None:
    with FirefoxWebDriverContextManager(headless) as driver:
        for name, value in URL_AND_CSV_PATH_MAPPING.items():
            try:
                file_name = value[0]
                url = value[1]
                products = parse_page(driver, url, name)
                save_product_to_csv(file_name, products)
            except Exception as e:
                print(e)


if __name__ == "__main__":
    get_all_products(headless=True)
