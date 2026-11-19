import csv
from dataclasses import dataclass
from urllib.parse import urljoin
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


def get_all_products() -> None:
    options = Options()
    options.add_argument("--headless")

    driver = webdriver.Chrome(options=options)

    pages = {
        "home": "",
        "computers": "computers",
        "laptops": "computers/laptops",
        "tablets": "computers/tablets",
        "phones": "phones",
        "touch": "phones/touch",
    }

    try:
        for name, path in pages.items():
            driver.get(urljoin(HOME_URL, path))

            accept_button = driver.find_elements(
                By.CSS_SELECTOR, "button[data-tid='banner-accept']"
            )

            if accept_button:
                WebDriverWait(driver, 10).until(
                    ec.element_to_be_clickable(
                        (By.CSS_SELECTOR, "button[data-tid='banner-accept']")
                    )
                ).click()

                WebDriverWait(driver, 10).until(
                    ec.invisibility_of_element_located(
                        (
                            By.CSS_SELECTOR,
                            "[data-termly-part='consent-banner']"
                        )
                    )
                )

            products = []

            while True:
                cards = driver.find_elements(
                    By.CLASS_NAME, "thumbnail"
                )

                for card in cards[len(products):]:
                    title = card.find_element(
                        By.CLASS_NAME, "title"
                    ).get_attribute("title")

                    description = card.find_element(
                        By.CLASS_NAME, "description"
                    ).text

                    price = float(
                        card.find_element(
                            By.CLASS_NAME, "price"
                        ).text.replace("$", "")
                    )

                    rating = len(
                        card.find_elements(
                            By.CLASS_NAME, "ws-icon-star"
                        )
                    )

                    reviews = int(
                        card.find_element(
                            By.CLASS_NAME, "ratings"
                        ).find_element(
                            By.TAG_NAME, "p"
                        ).text.split()[0]
                    )

                    products.append(
                        Product(
                            title,
                            description,
                            price,
                            rating,
                            reviews,
                        )
                    )

                visible_buttons = [
                    btn
                    for btn in driver.find_elements(
                        By.CLASS_NAME,
                        "ecomerce-items-scroll-more"
                    )
                    if btn.is_displayed()
                ]

                if not visible_buttons:
                    break

                old_count = len(cards)
                button = visible_buttons[0]

                driver.execute_script(
                    "arguments[0].scrollIntoView({block: 'center'});",
                    button,
                )

                WebDriverWait(driver, 10).until(
                    ec.element_to_be_clickable(button)
                ).click()

                try:
                    WebDriverWait(driver, 10).until(
                        lambda d: len(
                            d.find_elements(By.CLASS_NAME,
                                            "thumbnail"
                                            )
                        ) > old_count
                    )
                except TimeoutException:
                    break

            with open(
                f"{name}.csv",
                "w",
                newline="",
                encoding="utf-8"
            ) as file:
                writer = csv.writer(file)

                writer.writerow([
                    "title",
                    "description",
                    "price",
                    "rating",
                    "num_of_reviews",
                ])

                for product in products:
                    writer.writerow([
                        product.title,
                        product.description,
                        product.price,
                        product.rating,
                        product.num_of_reviews,
                    ])

    finally:
        driver.quit()


if __name__ == "__main__":
    get_all_products()
