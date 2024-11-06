import csv
from dataclasses import dataclass
from urllib.parse import urljoin

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.wait import WebDriverWait


BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more")
COMPUTERS_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/computers")
LAPTOPS_URL = urljoin(
    BASE_URL, "test-sites/e-commerce/more/computers/laptops"
)
TABLETS_URL = urljoin(
    BASE_URL, "test-sites/e-commerce/more/computers/tablets"
)
PHONES_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/phones")
TOUCH_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/phones/touch")


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


def parse_product(product_element: WebElement) -> Product:
    return Product(
        title=product_element.find_element(
            By.CLASS_NAME, "title"
        ).get_attribute("title"),
        description=product_element.find_element(
            By.CLASS_NAME, "description"
        ).text,
        price=float(
            product_element.find_element(
                By.CLASS_NAME, "price"
            ).text.replace("$", "")
        ),
        rating=len(
            product_element.find_elements(
                By.CLASS_NAME, "ws-icon-star"
            )
        ),
        num_of_reviews=int(
            product_element.find_element(
                By.CLASS_NAME, "review-count"
            ).text.split()[0]
        ),
    )


def get_all_products_from_page(page_url: str) -> list[Product]:
    with webdriver.Chrome() as driver:
        driver.get(page_url)

        try:
            cookie_banner = WebDriverWait(driver, 10).until(
                ec.visibility_of_element_located((By.ID, "cookieBanner"))
            )
            if cookie_banner:
                close_button = cookie_banner.find_element(
                    By.ID, "closeCookieBanner"
                )
                close_button.click()
        except Exception as e:
            print("Couldn't close Cookie Banner:", e)

        try:
            while True:
                more_buttons = driver.find_elements(
                    By.CLASS_NAME, "ecomerce-items-scroll-more"
                )
                if not more_buttons:
                    break

                more_button = more_buttons[0]
                if more_button.value_of_css_property("display") == "none":
                    break

                WebDriverWait(driver, 10).until(
                    ec.element_to_be_clickable(more_button)
                )
                more_button.click()
        except Exception as e:
            print("Exception:", e)

        product_elements = driver.find_elements(
            By.CLASS_NAME, "product-wrapper"
        )

        return [
            parse_product(product_element)
            for product_element in product_elements
        ]


def get_all_products() -> None:
    products = {
        "home.csv": get_all_products_from_page(HOME_URL),
        "computers.csv": get_all_products_from_page(COMPUTERS_URL),
        "laptops.csv": get_all_products_from_page(LAPTOPS_URL),
        "tablets.csv": get_all_products_from_page(TABLETS_URL),
        "phones.csv": get_all_products_from_page(PHONES_URL),
        "touch.csv": get_all_products_from_page(TOUCH_URL)
    }

    write_products_to_csv(products)


def write_products_to_csv(data: dict[str, list[Product]]) -> None:
    for csv_file_name, products_list in data.items():
        with open(csv_file_name, "w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(
                ["title", "description", "price", "rating", "num_of_reviews"]
            )

            for product in products_list:
                writer.writerow(
                    [
                        product.title,
                        product.description,
                        product.price,
                        product.rating,
                        product.num_of_reviews
                    ]
                )


if __name__ == "__main__":
    get_all_products()
