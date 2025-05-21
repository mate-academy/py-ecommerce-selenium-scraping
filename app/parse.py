import csv
import json
from dataclasses import dataclass, fields
from urllib.parse import urljoin
from time import sleep

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
PHONE_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/phones/")
TOUCH_URL = urljoin(BASE_URL, "/test-sites/e-commerce/more/phones/touch/")
COMPUTER_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/computers/")
TABLET_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/computers/tablets/")
LAPTOP_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/computers/laptops/")

URL_AND_CSV_PATH = {
    "home": ["home.csv", HOME_URL],
    "phones": ["phones.csv", PHONE_URL],
    "touch": ["touch.csv", TOUCH_URL],
    "computers": ["computers.csv", COMPUTER_URL],
    "tablets": ["tablets.csv", TABLET_URL],
    "laptops": ["laptops.csv", LAPTOP_URL],
}

OPTIONS_WEB_DRIVER = webdriver.ChromeOptions()
OPTIONS_WEB_DRIVER.add_argument("--headless=new")


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int
    additional_info: dict


def get_ellement_bool(
        by: By, value: str, element: WebElement
) -> WebElement | bool:
    try:
        return element.find_element(by, value)
    except NoSuchElementException:
        return False


def click_cookie_button(driver: WebElement) -> None:
    cookie = get_ellement_bool(
        by=By.CLASS_NAME, value="acceptContainer", element=driver
    )

    if cookie:
        cookie_button = cookie.find_element(By.TAG_NAME, "button")
        WebDriverWait(driver, 0.5).until(
            expected_conditions.element_to_be_clickable(cookie_button)
        )
        cookie_button.click()


def click_scroll_button(draiver: WebElement) -> None:
    scroll = get_ellement_bool(
        element=draiver,
        by=By.CLASS_NAME,
        value="ecommerce-items-scroll-more"
    )
    while scroll and scroll.is_displayed():
        scroll.click()
        sleep(0.1)


def get_price_by_hdd(element: WebElement,
                     driver: WebElement) -> dict[str, float]:
    hdd_price = {}

    buttons = element.find_elements(By.TAG_NAME, "button")

    for button in buttons:
        if not button.get_property("disabled"):
            button.click()
            hdd_price[button.get_property("value")] = float(
                driver.find_element(
                    By.CLASS_NAME, "price"
                ).text.replace("$", "")
            )
    return hdd_price


def get_product_colors(element: WebElement) -> list[str]:
    colors = []

    items = element.find_elements(By.CLASS_NAME, "dropdown-item")
    for item in items[1:]:
        colors.append(item.get_property("value"))
    return colors


def get_product_additional_info(driver: WebElement, product: Tag) -> dict:
    url = urljoin(BASE_URL, product.select_one(".title")["href"])
    info = {}

    driver.get(url)
    click_cookie_button(driver)
    product = driver.find_element(By.CLASS_NAME, "cart_body")

    hdd_element = get_ellement_bool(
        element=product,
        by=By.CLASS_NAME,
        value="swatches"
    )
    if hdd_element:
        info["hdd"] = get_price_by_hdd(
            element=hdd_element,
            driver=driver
        )
    color_element = get_ellement_bool(
        element=product,
        by=By.CLASS_NAME,
        value="dropdown"
    )
    if color_element:
        info["colors"] = get_product_colors(color_element)
    return info


def parse_product(product: Tag, driver: WebElement) -> Product:
    return Product(
        title=product.select_one(".title")["title"],
        description=product.select_one(".description").text,
        price=float(product.select_one(".price").text.replace("$", "")),
        rating=len(product.select(".ws-icon-star")),
        num_of_reviews=int(product.select_one(".reviews").text.split()[0]),
        additional_info=get_product_additional_info(driver, product)
    )


def parse_page(page_url: str, name_process: str) -> list[Product]:
    with webdriver.Chrome(options=OPTIONS_WEB_DRIVER) as driver:
        driver.get(page_url)
        click_cookie_button(driver)
        click_scroll_button(driver)
        html = driver.page_source

        soup = BeautifulSoup(html, "html.parser")
        product_soup = soup.select(".card_body")

        products = []

        for product in tqdm(
            product_soup,
            desc=f"Parsing {name_process.title()}",
        ):
            products.append(parse_product(product, driver))
        return products


def save_in_csv(file_name: str, objects: list[Product]) -> None:
    with open(file_name, "w", encoding="UTF-8", newline="") as f:
        if objects:
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
        save_in_csv(file_name, products)


if __name__ == "__main__":
    get_all_products()
