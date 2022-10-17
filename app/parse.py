import csv
from dataclasses import dataclass, fields, astuple
from urllib.parse import urljoin
import requests
import selenium
from bs4 import BeautifulSoup, Tag
from selenium.common import TimeoutException
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium import webdriver
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")

COMPUTERS_URL = urljoin(HOME_URL, "computers/")
LAPTOPS_URL = urljoin(COMPUTERS_URL, "laptops")
TABLETS_URL = urljoin(COMPUTERS_URL, "tablets")

PHONES_URL = urljoin(HOME_URL, "phones/")
TOUCH_URL = urljoin(PHONES_URL, "touch")

STATIC_PAGES = {
    "home.csv": HOME_URL,
    "computers.csv": COMPUTERS_URL,
    "phones.csv": PHONES_URL,
    "laptops.csv": LAPTOPS_URL,
    "tablets.csv": TABLETS_URL,
    "touch.csv": TOUCH_URL,
}


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


PRODUCT_FIELDS = [field.name for field in fields(Product)]


def driver_open() -> WebDriver:
    driver = webdriver.Chrome(ChromeDriverManager().install())

    return driver


def driver_close(driver: WebDriver()) -> None:
    driver.close()


def get_single_product(soup: Tag) -> Product:
    return Product(
        title=soup.select_one(".title")["title"],
        description=soup.select_one(".description").text,
        price=float(soup.select_one(".price").text.replace("$", "")),
        rating=int(soup.select_one(".ratings p[data-rating]")["data-rating"])
        if soup.select_one(".ratings p[data-rating]") else 5,
        num_of_reviews=int(soup.select_one(
            ".ratings .pull-right").text.split()[0]),

    )


def parse_page(file_name: str, url: str) -> list:
    driver = driver_open()
    try:
        cookies = driver.find_element(By.CLASS_NAME, "acceptCookies")
        if cookies.is_displayed():
            cookies.click()
    except selenium.common.exceptions.NoSuchElementException:
        pass
    page = requests.get(url).content
    btn_pagination = BeautifulSoup(page, "html.parser").select_one(
        "div.container.test-site > div > div.col-md-9 > a")
    if btn_pagination:
        driver.get(url)
        button = driver.find_element(
            By.CSS_SELECTOR,
            "div.container.test-site > div > div.col-md-9 > a")
        wait = WebDriverWait(driver, 10)
        while button.is_displayed():
            try:
                elem = wait.until(
                    expected_conditions.visibility_of_element_located(
                        (By.XPATH, "/html/body/div[1]/div[3]/div/div[2]/a")),
                    "Cannot find 'Load More' button")
                driver.execute_script("arguments[0].click()", elem)

            except TimeoutException:
                break

        page = driver.page_source.encode("utf-8")
        driver_close(driver)
    soup = BeautifulSoup(page, "html.parser").select(".thumbnail")
    return [[get_single_product(product) for product in soup], file_name]


def get_all_products() -> list:
    pages = [parse_page(file_name, url)
             for file_name, url in STATIC_PAGES.items()
             ]
    return [products_to_scv(page[0], page[1]) for page in pages]


def products_to_scv(products: list[Product], file_name: str) -> None:
    with open(file_name, "w", encoding="ISO-8859-1", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(PRODUCT_FIELDS)
        writer.writerows([astuple(product) for product in products])


if __name__ == "__main__":
    get_all_products()
