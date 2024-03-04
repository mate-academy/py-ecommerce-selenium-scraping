import csv
from dataclasses import dataclass, fields, astuple
from urllib.parse import urljoin

# BeautifulSoup for parsing HTML
from bs4 import BeautifulSoup
from selenium import webdriver
# Selenium imports for web scraping automation
from selenium.common import NoSuchElementException
from selenium.webdriver.common.by import By

# Import ChromeDriver from custom module
from app.driver import ChromeDriver

# Base URL for the website
BASE_URL = "https://webscraper.io/"
# URL for the home page of the e-commerce test site
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more")

# Dictionary to map page names to their respective paths
name_path = {
    "home": "/",
    "computers": "/computers",
    "laptops": "/computers/laptops",
    "tablets": "/computers/tablets",
    "phones": "/phones",
    "touch": "/phones/touch",
}


@dataclass
class Product:
    """Dataclass representing a product with its attributes"""

    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int

    @classmethod
    def field(cls) -> list[str]:
        """Class method to get the names of fields in the dataclass"""
        return [field.name for field in fields(cls)]


def parse_single_product(product: BeautifulSoup) -> Product:
    """Function to parse a single product from its HTML representation"""
    return Product(
        title=product.select_one(".title")["title"],
        description=product.select_one(
            ".description").text.replace("\xa0", " "),
        price=float(product.select_one(".price").text.replace("$", "")),
        rating=int(len(product.select_one("div.ratings").contents[1])),
        num_of_reviews=int(
            product.select_one("div.ratings > p.review-count").text.split()[0]
        ),
    )


def get_page_all_products(page_soup: BeautifulSoup) -> [Product]:
    """Function to get all products from a page's HTML"""
    return [parse_single_product(product)
            for product in page_soup.select(".card-body")
            ]


def parse_all_products_on_page(url: str, driver: webdriver) -> [Product]:
    """Function to parse all products on a given page URL using Selenium"""
    driver.get(url)

    # Scroll down to load all products on the page
    while True:
        try:
            button_more = driver.find_element(
                By.CLASS_NAME, "ecomerce-items-scroll-more"
            )
            tag_style = button_more.get_property("style")

            # "style" attribute indicates there are no more products to load
            if len(tag_style) == 1:
                break
            driver.execute_script("arguments[0].click();", button_more)
        except NoSuchElementException:
            break

    # Parse products from the loaded HTML
    return get_page_all_products(
        BeautifulSoup(driver.page_source, "html.parser"))


def add_products_to_csv(products: [Product], output_csv_path: str) -> None:
    """Function to add products to a CSV file"""
    with open(output_csv_path, "w") as file:
        writer = csv.writer(file)
        writer.writerow(Product.field())  # Write header row with field names
        # Write product data to CSV
        writer.writerows([astuple(product) for product in products])


def get_all_products() -> [Product]:
    """Function to get all products from the e-commerce site"""
    # Initialize ChromeDriver instance
    driver = ChromeDriver()

    # Iterate over the pages and scrape products, saving them to CSV files
    for name, path in name_path.items():
        add_products_to_csv(
            products=parse_all_products_on_page(f"{HOME_URL}{path}", driver),
            output_csv_path=f"{name}.csv",
        )


if __name__ == "__main__":
    get_all_products()  # Call the function to scrape and save products
