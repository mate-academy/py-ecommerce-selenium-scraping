import csv
from dataclasses import dataclass, astuple, fields
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common import NoSuchElementException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait
from tqdm import tqdm

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


def accept_cookies(driver: WebDriver) -> None:
    """Accepting cookies on Homepage if necessary"""

    try:
        element = WebDriverWait(driver, 5).until(
            ec.presence_of_element_located((By.CLASS_NAME, "acceptCookies"))
        )
        element.click()
    except Exception as e:
        print("Cookie consent button not found or failed to click:", e)


def parse_single_product(product_soup: BeautifulSoup) -> Product:
    """Parsing single product from beautifulsoup instance"""

    return Product(
        title=product_soup.select_one(".title")["title"],
        description=product_soup.select_one(".description").text,
        price=float(product_soup.select_one(".price").text.replace("$", "")),
        rating=len(product_soup.select(".ws-icon.ws-icon-star")),
        num_of_reviews=int(product_soup.select_one(
            ".ratings > p.float-end"
        ).text.split()[0])
    )


def get_single_page_products(page_soup: BeautifulSoup) -> [Product]:
    """Getting all products as list from beautifulsoup instance"""

    products = page_soup.select(".thumbnail")

    return [parse_single_product(product_soup) for product_soup in products]


def click_more_button(driver: WebDriver) -> None:
    """Clicking `more` button, if necessary, until it disappeared"""

    more_button = driver.find_element(
        By.CLASS_NAME,
        "btn.btn-lg.btn-block.btn-primary.ecomerce-items-scroll-more"
    )
    while not more_button.get_property("style"):
        driver.execute_script("arguments[0].click();", more_button)


def write_products_to_csv(products: [Product], file_name: str) -> None:
    """Creating .csv file and saving info about products"""

    with open(f"{file_name.lower()}.csv", "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(PRODUCT_FIELDS)
        writer.writerows([astuple(product) for product in products])


def get_page_soup(driver: WebDriver) -> BeautifulSoup:
    """Creating beautifulsoup instance from driver"""

    html_content = driver.page_source
    return BeautifulSoup(html_content, "html.parser")


def get_soup_write_to_file(driver: WebDriver, file_name: str) -> None:
    """Connected 3 functions in one to follow DRY"""

    page_soup = get_page_soup(driver)
    products = get_single_page_products(page_soup)
    write_products_to_csv(products=products, file_name=file_name)


def create_driver_with_headless() -> WebDriver:
    """Creating WebDriver instance with headless option
     to run Selenium without opening a browse"""

    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    return webdriver.Chrome(options=chrome_options)


def get_all_products() -> None:
    # Creating driver, running Homepage and accepting cookies
    driver = create_driver_with_headless()
    driver.get(HOME_URL)
    accept_cookies(driver=driver)

    # Tacking main categories as `items`
    selector = driver.find_element(By.CLASS_NAME, "nav.flex-column")
    items = selector.find_elements(By.CLASS_NAME, "nav-item")

    # Saving products to files for every category in items
    for item in tqdm(items, desc="Processing", unit="item"):
        file_name = item.text
        get_soup_write_to_file(driver=driver, file_name=file_name)

        # Checking, if category has subcategory and,
        # if it has, following category's-page
        try:
            url = item.find_element(
                By.CLASS_NAME,
                "category-link.nav-link"
            ).get_property("href")
            driver.get(url)
            subcategories = driver.find_elements(
                By.CLASS_NAME,
                "nav-link.subcategory-link"
            )

            # Follow every subcategory's-page,
            # open whole page with `more`-button,
            # taking all products from it and saving to files.
            for subcategory in subcategories:
                sub_url = subcategory.get_property("href")
                file_name = subcategory.text
                driver.get(sub_url)
                click_more_button(driver=driver)

                get_soup_write_to_file(driver=driver, file_name=file_name)

                driver.back()
            driver.back()
        except NoSuchElementException:
            pass
    driver.close()


if __name__ == "__main__":
    get_all_products()
