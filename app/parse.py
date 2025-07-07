from dataclasses import dataclass, fields
from time import sleep
from urllib.parse import urljoin

from bs4 import Tag, BeautifulSoup
from selenium import webdriver
from selenium.common import TimeoutException
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")

COMPUTERS_URL = urljoin(HOME_URL, "computers/")
TABLETS_URL = urljoin(COMPUTERS_URL, "tablets")
LAPTOPS_URL = urljoin(COMPUTERS_URL, "laptops")

PHONES_URL = urljoin(HOME_URL, "phones/")
TOUCH_URL = urljoin(PHONES_URL, "touch")


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


PRODUCT_FIELDS = [field.name for field in fields(Product)]


def get_driver() -> WebDriver:
    return driver_


def set_driver(new_driver: WebDriver) -> None:
    global driver_
    driver_ = new_driver


def accept_cookies() -> None:
    driver = get_driver()
    driver.get(HOME_URL)
    cookie_button = (By.CLASS_NAME, "acceptCookies")

    WebDriverWait(driver, 5).until(
        EC.visibility_of_element_located((cookie_button))
    )
    driver.find_element(*cookie_button).click()


def load_full_page(url: str) -> str:
    driver = get_driver()
    driver.get(url)
    button_class = (By.CLASS_NAME, "ecomerce-items-scroll-more")

    while True:
        sleep(1)
        buttons = driver.find_elements(*button_class)
        if not buttons:
            break

        button = buttons[0]
        try:
            WebDriverWait(driver, 1).until(
                EC.visibility_of_element_located((button_class))
            )
        except TimeoutException:
            break

        if (
            buttons
            and button.is_displayed()
            and button.is_enabled()
            and button.value_of_css_property("display") != "none"
        ):
            driver.execute_script(
                "arguments[0].scrollIntoView({block:'center'});", button
            )
            try:
                WebDriverWait(driver, 1).until(
                    EC.element_to_be_clickable(button)
                )
            except TimeoutException:
                break
            button.click()
        else:
            break
    return driver.page_source


def get_products(url: str) -> list[Product]:
    page_source = load_full_page(url)
    soup = BeautifulSoup(page_source, "html.parser")
    result = soup.select(".card-body")
    products = [productify(product) for product in result]
    return products


def productify(data: Tag) -> Product:
    title = data.select_one("a.title")["title"]
    description = data.select_one("p.description").text
    price = float(data.select_one("h4.price").text.replace("$", ""))
    rating_data = data.select_one(".ratings")
    rating = len(rating_data.select("span.ws-icon-star"))
    num_of_reviews = int(
        rating_data.find("span", attrs={"itemprop": "reviewCount"}).text
    )
    return Product(title, description, price, rating, num_of_reviews)


def get_all_products() -> None:
    with webdriver.Chrome() as driver:
        set_driver(driver)
        accept_cookies()
        home = ("home.csv", get_products(HOME_URL))
        computers = ("computers.csv", get_products(COMPUTERS_URL))
        tablets = ("tablets.csv", get_products(TABLETS_URL))
        laptops = ("laptops.csv", get_products(LAPTOPS_URL))
        phones = ("phones.csv", get_products(PHONES_URL))
        touch = ("touch.csv", get_products(TOUCH_URL))
        print(laptops)


if __name__ == "__main__":
    get_all_products()
