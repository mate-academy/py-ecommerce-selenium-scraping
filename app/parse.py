import csv
import time
from dataclasses import dataclass, astuple
from urllib.parse import urljoin
from selenium import webdriver
from selenium.common import NoSuchElementException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")
COMPUTERS_URL = urljoin(HOME_URL, "computers/")
LAPTOPS_URL = urljoin(COMPUTERS_URL, "laptops")
TABLETS_URL = urljoin(COMPUTERS_URL, "tablets")
PHONES_URL = urljoin(HOME_URL, "phones/")
TOUCH_URL = urljoin(HOME_URL, "touch")


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


def make_chrome_driver() -> webdriver:
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    return webdriver.Chrome(options=chrome_options)


def parse_page(products: list[webdriver]) -> list[Product]:
    products_list = []

    for product in products:
        products_list.append(Product(
            title=product.find_element(
                By.CLASS_NAME, "title").get_attribute("title"),
            description=product.find_element(
                By.CLASS_NAME, "description").text,
            price=float(product.find_element(
                By.CLASS_NAME, "price").text.replace("$", "")),
            rating=len(product.find_elements(By.CLASS_NAME, "glyphicon")),
            num_of_reviews=int(product.find_element(
                By.CLASS_NAME, "ratings").text.split()[0]),
        ))

    return products_list


def write_csv_files(file_name: str, products: list[Product]) -> None:
    headers = vars(Product)["__match_args__"]
    output_csv_path = file_name.split("_")[0].lower() + ".csv"

    with open(output_csv_path, "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(headers)
        writer.writerows([astuple(product) for product in products])


def get_all_products() -> None:
    urls = {k: v for k, v in globals().items() if "URL" in k}
    urls.pop("BASE_URL")

    for file_name, url in urls.items():
        with make_chrome_driver() as driver:
            driver.get(url)

            try:
                button = driver.find_element(
                    By.CLASS_NAME, "ecomerce-items-scroll-more"
                )

                try:
                    cookies = driver.find_element(
                        By.CLASS_NAME, "acceptCookies"
                    )
                    (webdriver.ActionChains(driver)
                     .move_to_element(cookies).click(cookies).perform())
                except NoSuchElementException:
                    continue

                while not button.get_attribute("style"):
                    (webdriver.ActionChains(driver)
                     .move_to_element(button).click(button).perform())
                    time.sleep(0.1)

            except NoSuchElementException:
                continue
            finally:
                products = driver.find_elements(By.CLASS_NAME, "thumbnail")
                write_csv_files(file_name=file_name,
                                products=parse_page(products))


if __name__ == "__main__":
    get_all_products()
