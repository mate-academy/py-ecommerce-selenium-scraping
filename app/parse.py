from dataclasses import dataclass
from urllib.parse import urljoin
import csv
import time
import logging

from bs4 import BeautifulSoup, Tag
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")

options = Options()
options.add_argument("--headless")
driver = webdriver.Chrome(options=options)


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int
    additional_info: dict


def parse_hdd_block_prices(product_soup: Tag) -> dict[str, float]:
    absolute_url = urljoin(
        BASE_URL,
        product_soup.select_one(".title")["href"]
    )

    options = Options()
    options.add_argument("--headless")
    local_driver = webdriver.Chrome(options=options)
    local_driver.get(absolute_url)

    try:
        try:
            WebDriverWait(local_driver, 3).until(
                expected_conditions.element_to_be_clickable(
                    (By.CLASS_NAME, "accept-cookies")
                )
            ).click()
            time.sleep(0.5)
        except Exception:
            pass

        swatches = local_driver.find_element(By.CLASS_NAME, "swatches")
        buttons = swatches.find_elements(By.TAG_NAME, "button")

        prices = {}
        for button in buttons:
            if not button.get_property("disabled"):
                try:
                    local_driver.execute_script(
                        "arguments[0].scrollIntoView(true);",
                        button
                    )
                    time.sleep(0.2)
                    local_driver.execute_script(
                        "arguments[0].click();",
                        button
                    )
                    time.sleep(0.3)
                    value = button.get_property("value")
                    price_element = local_driver.find_element(
                        By.CLASS_NAME,
                        "price"
                    )
                    price = float(price_element.text.replace("$", ""))
                    prices[value] = price
                except Exception as e:
                    logger.warning(f"Failed to click HDD button: {e}")
                    continue
    except Exception as e:
        logger.warning(f"Failed to parse HDD prices: {e}")
        prices = {}
    finally:
        local_driver.quit()
    return prices


def parse_single_product(product: Tag) -> Product:
    try:
        hdd_prices = parse_hdd_block_prices(product)

        title_tag = product.select_one(".title")
        desc_tag = product.select_one(".description")
        price_tag = product.select_one(".price")
        rating_tag = product.select_one("p[data-rating]")
        review_tag = product.select_one(".review-count")

        return Product(
            title=title_tag["title"] if title_tag else "",
            description=desc_tag.text if desc_tag else "",
            price=float(price_tag.text.replace("$", ""))
            if price_tag else 0.0,
            rating=int(rating_tag["data-rating"]) if rating_tag else 0,
            num_of_reviews=int(
                review_tag.text.split()[0]
            ) if review_tag else 0,
            additional_info={"hdd_prices": hdd_prices},
        )
    except Exception as e:
        logger.error(f"Failed to parse product: {e}")
        return Product("", "", 0.0, 0, 0, {})


def write_csv(filename: str, products: list[Product]) -> None:
    try:
        with open(
            f"{filename}.csv",
            mode="w",
            newline="",
            encoding="utf-8"
        ) as f:
            writer = csv.writer(f)
            writer.writerow(Product.__annotations__.keys())
            for product in products:
                writer.writerow(
                    [
                        product.title,
                        product.description,
                        product.price,
                        product.rating,
                        product.num_of_reviews,
                        product.additional_info,
                    ]
                )
        logger.info(f"Successfully wrote {len(products)} products to "
                    f"{filename}.csv")
    except Exception as e:
        logger.error(f"Failed to write CSV file {filename}.csv: {e}")


def get_products_from_page(page_url: str) -> list[Product]:
    try:
        driver.get(page_url)
        logger.info(f"Loading page: {page_url}")

        try:
            WebDriverWait(driver, 3).until(
                expected_conditions.element_to_be_clickable(
                    (By.CLASS_NAME, "accept-cookies")
                )
            ).click()
            logger.info("Accepted cookies")
        except Exception:
            pass

        while True:
            try:
                load_more = WebDriverWait(driver, 2).until(
                    expected_conditions.element_to_be_clickable(
                        (By.CLASS_NAME, "btn-primary")
                    )
                )
                driver.execute_script("arguments[0].click();", load_more)
                time.sleep(0.5)
            except Exception:
                break

        soup = BeautifulSoup(driver.page_source, "html.parser")
        product_tags = soup.select(".card-body")
        logger.info(f"Found {len(product_tags)} products on page")

        return [parse_single_product(tag) for tag in product_tags]
    except Exception as e:
        logger.error(f"Failed to get products from page {page_url}: {e}")
        return []


def get_all_products() -> None:
    pages = {
        "home": HOME_URL,
        "computers": urljoin(HOME_URL, "computers"),
        "laptops": urljoin(HOME_URL, "computers/laptops"),
        "tablets": urljoin(HOME_URL, "computers/tablets"),
        "phones": urljoin(HOME_URL, "phones"),
        "touch": urljoin(HOME_URL, "phones/touch"),
    }

    for name, url in pages.items():
        print(f"Scraping {name} page...")
        products = get_products_from_page(url)
        write_csv(name, products)
        print(f"Completed scraping {name} page "
              f"- saved {len(products)} products")


if __name__ == "__main__":
    try:
        get_all_products()
    except Exception as e:
        logger.error(f"An error occurred during scraping: {e}")
    finally:
        driver.quit()
        logger.info("Scraping completed")
