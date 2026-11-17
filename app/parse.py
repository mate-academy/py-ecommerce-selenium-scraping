import csv
from dataclasses import dataclass
from urllib.parse import urljoin

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait


BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")

PAGES = {
    "home": HOME_URL,
    "computers": urljoin(HOME_URL, "computers"),
    "laptops": urljoin(HOME_URL, "computers/laptops"),
    "tablets": urljoin(HOME_URL, "computers/tablets"),
    "phones": urljoin(HOME_URL, "phones"),
    "touch": urljoin(HOME_URL, "phones/touch"),
}


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


def save_products_to_csv(
    products: list[Product],
    filename: str
) -> None:
    with open(filename, "w", newline="") as file:
        writer = csv.writer(file)

        writer.writerow([
            "title",
            "description",
            "price",
            "rating",
            "num_of_reviews"
        ])

        for product in products:
            writer.writerow([
                product.title,
                product.description,
                product.price,
                product.rating,
                product.num_of_reviews
            ])


def scrape_page(url: str, filename: str) -> None:
    driver = webdriver.Chrome()

    try:
        driver.get(url)

        accept_buttons = driver.find_elements(
            By.XPATH,
            "//button[normalize-space()='Accept']"
        )

        if accept_buttons:
            accept_buttons[0].click()

        while True:
            more_buttons = driver.find_elements(
                By.CSS_SELECTOR,
                "a.ecomerce-items-scroll-more"
            )

            if not more_buttons:
                break

            if (
                not more_buttons[0].is_displayed()
                or not more_buttons[0].is_enabled()
            ):
                break

            old_count = len(
                driver.find_elements(By.CSS_SELECTOR, ".thumbnail")
            )

            more_buttons[0].click()

            WebDriverWait(driver, 10).until(
                lambda d: len(
                    d.find_elements(By.CSS_SELECTOR, ".thumbnail")
                ) > old_count
            )

            print(
                "Завантажено товарів:",
                len(driver.find_elements(By.CSS_SELECTOR, ".thumbnail"))
            )

        products = driver.find_elements(
            By.CSS_SELECTOR,
            ".thumbnail"
        )

        print(f"Found products: {len(products)}")

        all_products = []

        for product_card in products:
            title = product_card.find_element(
                By.CSS_SELECTOR,
                ".title"
            )

            description = product_card.find_element(
                By.CSS_SELECTOR,
                ".description"
            )

            price = product_card.find_element(
                By.CSS_SELECTOR,
                ".price"
            )
            price_value = float(price.text.replace("$", ""))

            rating = product_card.find_element(
                By.CSS_SELECTOR,
                ".ratings"
            )

            rating_value = len(
                rating.find_elements(
                    By.CSS_SELECTOR,
                    ".ws-icon-star"
                )
            )

            reviews_value = int(rating.text.split()[0])

            product = Product(
                title=title.get_attribute("title"),
                description=description.text,
                price=price_value,
                rating=rating_value,
                num_of_reviews=reviews_value
            )

            all_products.append(product)

        save_products_to_csv(all_products, filename)

    finally:
        driver.quit()


def get_all_products() -> None:
    for page, url in PAGES.items():
        filename = f"{page}.csv"
        scrape_page(url, filename)


if __name__ == "__main__":
    get_all_products()
