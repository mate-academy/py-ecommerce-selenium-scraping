import csv
from dataclasses import dataclass, fields, asdict
from urllib.parse import urljoin

from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver import Chrome, ChromeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


def init_driver() -> Chrome:
    """
    Initializes a Chrome driver with headless mode enabled and necessary arguments set.

    Returns:
        Chrome: The initialized Chrome driver.
    """  # noqa: E501
    options = ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--no-sandbox")

    driver = Chrome(options=options)
    return driver


def get_product(product_card: WebElement) -> Product:
    """
    Parses information from a product card WebElement and creates a Product object.

    Args:
        product_card (WebElement): The WebElement representing a product card.

    Returns:
        Product: An instance of the Product class containing the parsed information.
    """  # noqa: E501
    title = (
        product_card
        .find_element(By.CLASS_NAME, "title")
        .get_attribute("title")
    )
    description = (
        product_card
        .find_element(By.CLASS_NAME, "description")
        .text
    )
    price = float(
        product_card
        .find_element(By.CLASS_NAME, "price")
        .text
        .replace("$", "")
    )
    rating = len(
        product_card
        .find_elements(By.CLASS_NAME, "ws-icon-star")
    )
    num_of_reviews = int(
        product_card
        .find_element(By.CLASS_NAME, "ratings")
        .text
        .split(" ")[0]
    )
    return Product(
        title,
        description,
        price,
        rating,
        num_of_reviews
    )


def execute_more_pagination_script(driver: Chrome, max_products: int) -> None:
    """
    Executes the pagination script for a Chrome driver to load more products until the maximum number of products is reached.

    Args:
        driver (Chrome): The Chrome driver to execute the script on.
        max_products (int): The maximum number of products to load.
    """  # noqa: E501
    while len(driver.find_elements(By.CLASS_NAME, "thumbnail")) < max_products:
        try:
            button_more = driver.find_element(
                By.CLASS_NAME,
                "ecomerce-items-scroll-more"
            )
            driver.execute_script(
                "arguments[0].click();",
                button_more
            )
        except NoSuchElementException:
            break


def parse_product_card(
        driver: Chrome,
        max_products: int = 3
) -> list[Product]:
    """
    Parses the product cards on a web page using a Chrome driver.

    Args:
        driver (Chrome): The Chrome driver to use for parsing the product cards.
        max_products (int, optional): The maximum number of product cards to parse. Defaults to 3.

    Returns:
        list[Product]: A list of Product objects representing the parsed product cards.
    """  # noqa: E501
    if max_products:
        execute_more_pagination_script(driver, max_products)
    products = driver.find_elements(By.CLASS_NAME, "thumbnail")
    return [get_product(product_card) for product_card in products]


def write_to_csv(products: list[Product], filename: str) -> None:
    """
    Writes a list of Product objects to a CSV file.

    Args:
        products (list[Product]): A list of Product objects to be written to the CSV file.
        filename (str): The name of the CSV file to write the Product objects to.
    """  # noqa: E501
    with open(filename, "w", newline="") as csvfile:
        headers = [field.name for field in fields(Product)]
        writer = csv.DictWriter(csvfile, headers)
        writer.writeheader()
        for obj in products:
            writer.writerow(asdict(obj))


def get_all_products() -> None:
    driver = init_driver()
    driver.get(HOME_URL)

    write_to_csv(parse_product_card(driver), "home.csv")
    driver.find_element(By.LINK_TEXT, "Computers").click()
    write_to_csv(parse_product_card(driver), "computers.csv")
    driver.find_element(By.LINK_TEXT, "Laptops").click()
    write_to_csv(parse_product_card(driver, 117), "laptops.csv")
    driver.find_element(By.LINK_TEXT, "Tablets").click()
    write_to_csv(parse_product_card(driver, 21), "tablets.csv")
    driver.find_element(By.LINK_TEXT, "Phones").click()
    write_to_csv(parse_product_card(driver), "phones.csv")
    driver.find_element(By.LINK_TEXT, "Touch").click()
    write_to_csv(parse_product_card(driver, 9), "touch.csv")


if __name__ == "__main__":
    get_all_products()
