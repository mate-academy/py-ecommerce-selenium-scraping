from __future__ import annotations
import csv
import time
from dataclasses import dataclass, fields
from pathlib import Path
from urllib.parse import urljoin
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC  # noqa: N812

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")

PROJECT_ROOT = Path(__file__).resolve().parent.parent


@dataclass
class Product:
    title: str
    description: str
    price: str
    rating: str
    num_of_reviews: str


def accept_cookies_if_present(driver: webdriver.Chrome) -> None:
    try:
        cookie_button = WebDriverWait(driver, 2).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, ".acceptCookies"))
        )
        cookie_button.click()
    except Exception:
        pass


def load_all_products(driver: webdriver.Chrome) -> None:
    while True:
        try:
            buttons = driver.find_elements(
                By.CSS_SELECTOR,
                ".ecommerces-items-load-more, .btn-primary, a.more-btn"
            )

            more_button = None
            for btn in buttons:
                if "more" in btn.text.lower():
                    more_button = btn
                    break

            if not more_button or not more_button.is_displayed():
                break

            driver.execute_script(
                "arguments[0].scrollIntoView({block: 'center'});",
                more_button
            )
            time.sleep(0.3)

            more_button.click()
            time.sleep(1.0)
        except Exception:
            break


def parse_single_page(driver: webdriver.Chrome, url: str) -> list[Product]:
    driver.get(url)
    accept_cookies_if_present(driver)

    load_all_products(driver)

    try:
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".thumbnail"))
        )
    except Exception:
        return []

    products = []
    product_elements = driver.find_elements(By.CSS_SELECTOR, ".thumbnail")

    for element in product_elements:
        try:
            title = (
                element.find_element(By.CSS_SELECTOR, ".title")
                .get_attribute("title")
                .strip()
            )
            if not title:
                title = element.find_element(
                    By.CSS_SELECTOR, ".title"
                ).text.strip()

            description = element.find_element(
                By.CSS_SELECTOR, ".description"
            ).text.strip()

            price_text = element.find_element(By.CSS_SELECTOR, ".price").text
            price_clean = price_text.replace("$", "").strip()
            price = (
                f"{price_clean}.0" if "." not in price_clean else price_clean
            )

            stars = element.find_elements(By.CSS_SELECTOR,
                                          ".ratings .glyphicon-star"
                                          )
            rating = str(len(stars))

            if rating == "0":
                rating_p = element.find_element(By.CSS_SELECTOR,
                                                ".ratings p:nth-child(2)"
                                                )
                rating_attr = rating_p.get_attribute("data-rating")
                if rating_attr:
                    rating = str(rating_attr).strip()
                else:
                    rating = str(
                        len(rating_p.find_elements(By.CSS_SELECTOR, "span"))
                    )

            reviews_text = element.find_element(
                By.CSS_SELECTOR, ".ratings .pull-right"
            ).text
            num_of_reviews = str(reviews_text.split()[0])

            products.append(
                Product(
                    title=title,
                    description=description,
                    price=price,
                    rating=rating,
                    num_of_reviews=num_of_reviews
                )
            )
        except Exception:
            continue

    return products


def save_to_csv(products: list[Product], filename: str) -> None:
    full_path = PROJECT_ROOT / filename
    with open(full_path, "w", newline="", encoding="utf-8") as f:
        field_names = [field.name for field in fields(Product)]
        writer = csv.DictWriter(f, fieldnames=field_names)

        writer.writeheader()
        for product in products:
            writer.writerow(product.__dict__)


def get_all_products() -> None:
    chrome_service = Service(executable_path="chromedriver.exe")

    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")

    driver = webdriver.Chrome(service=chrome_service, options=options)

    base_url = HOME_URL.rstrip("/")

    pages = {
        "home": base_url,
        "computers": f"{base_url}/computers",
        "laptops": f"{base_url}/computers/laptops",
        "tablets": f"{base_url}/computers/tablets",
        "phones": f"{base_url}/phones",
        "touch": f"{base_url}/phones/touch",
    }

    try:
        for page_name, url in pages.items():
            products = parse_single_page(driver, url)
            save_to_csv(products, f"{page_name}.csv")
    finally:
        driver.quit()
