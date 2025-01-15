import csv
import time
from dataclasses import dataclass
from urllib.parse import urljoin
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import (
    NoSuchElementException,
    TimeoutException,
    StaleElementReferenceException,
)
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
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


def get_all_products() -> None:
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    driver = webdriver.Chrome(options=options)
    driver.implicitly_wait(0.15)

    pages = {
        "home": HOME_URL,
        "computers": urljoin(
            BASE_URL, "test-sites/e-commerce/more/computers"
        ),
        "laptops": urljoin(
            BASE_URL, "test-sites/e-commerce/more/computers/laptops"
        ),
        "tablets": urljoin(
            BASE_URL, "test-sites/e-commerce/more/computers/tablets"
        ),
        "phones": urljoin(
            BASE_URL, "test-sites/e-commerce/more/phones"
        ),
        "touch": urljoin(
            BASE_URL, "test-sites/e-commerce/more/phones/touch"
        ),
    }

    for page_name, url in pages.items():
        print(f"Scraping page: {page_name} - {url}")
        driver.get(url)

        products = []
        pbar = tqdm(
            desc=f"Processing {page_name} page", unit="product"
        )
        total_thumbnails = set()

        while True:
            try:
                WebDriverWait(driver, 0.15).until(
                    ec.presence_of_all_elements_located(
                        (By.CLASS_NAME, "thumbnail")
                    )
                )
                thumbnails = driver.find_elements(
                    By.CLASS_NAME, "thumbnail"
                )
                print(
                    f"Found {len(thumbnails)} thumbnails on the current view."
                )

                for idx, thumb in enumerate(thumbnails):
                    try:
                        unique_id = f"{page_name}_{idx}"
                        if unique_id in total_thumbnails:
                            continue
                        total_thumbnails.add(unique_id)

                        title_element = thumb.find_element(
                            By.CLASS_NAME, "title"
                        )
                        title = title_element.get_attribute(
                            "title"
                        ).strip()
                        description = thumb.find_element(
                            By.CLASS_NAME, "description"
                        ).text.strip()
                        price_text = (
                            thumb.find_element(By.CLASS_NAME, "price")
                            .text.replace("$", "")
                            .strip()
                        )
                        price = float(price_text)
                        ratings_div = thumb.find_element(
                            By.CLASS_NAME, "ratings"
                        )
                        star_elements = ratings_div.find_elements(
                            By.CSS_SELECTOR,
                            "p:nth-of-type(2) .ws-icon.ws-icon-star",
                        )
                        rating = len(star_elements)
                        reviews_text = thumb.find_element(
                            By.CLASS_NAME, "ratings"
                        ).text
                        num_of_reviews = int(
                            reviews_text.split()[0]
                        )
                        product = Product(
                            title,
                            description,
                            price,
                            rating,
                            num_of_reviews,
                        )
                        products.append(product)
                        pbar.update(1)
                    except (
                        NoSuchElementException,
                        StaleElementReferenceException,
                        ValueError,
                    ) as e:
                        print(
                            f"Error processing product at index {idx}: {e}"
                        )
                        continue

            except TimeoutException:
                print("Timeout waiting for thumbnails.")
                break

            try:
                more_button = driver.find_element(
                    By.LINK_TEXT, "More"
                )
                driver.execute_script(
                    "arguments[0].scrollIntoView(true);",
                    more_button,
                )
                more_button.click()
                print("Clicked More button.")

                WebDriverWait(driver, 10).until(
                    lambda d: len(
                        d.find_elements(By.CLASS_NAME, "thumbnail")
                    )
                    > len(total_thumbnails)
                )
                time.sleep(1)
            except NoSuchElementException:
                print(
                    "No More button found. Finished scraping this page."
                )
                break
            except TimeoutException:
                print(
                    "Timed out waiting for new thumbnails to load after "
                    "clicking More."
                )
                break

        pbar.close()
        print(
            f"Total products scraped for {page_name}: {len(products)}"
        )

        with open(
            f"{page_name}.csv",
            mode="w",
            newline="",
            encoding="utf-8",
        ) as file:
            writer = csv.writer(file)
            writer.writerow(
                [
                    "title",
                    "description",
                    "price",
                    "rating",
                    "num_of_reviews",
                ]
            )
            for product in products:
                writer.writerow(
                    [
                        product.title,
                        product.description,
                        product.price,
                        product.rating,
                        product.num_of_reviews,
                    ]
                )
        print(f"Data written to {page_name}.csv\n")

    driver.quit()


if __name__ == "__main__":
    get_all_products()
