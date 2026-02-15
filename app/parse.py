import csv
from dataclasses import dataclass, fields
from urllib.parse import urljoin

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
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


def get_driver() -> webdriver.Chrome:
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--window-size=1920,1080")
    return webdriver.Chrome(options=options)


def clear_cookies(driver: webdriver.Chrome) -> None:
    try:
        WebDriverWait(driver, 3).until(
            ec.element_to_be_clickable((By.ID, "cookieBannerBtn"))
        ).click()
    except Exception:
        pass


def extract_page_data(driver: webdriver.Chrome) -> list[Product]:
    results = []
    items = driver.find_elements(By.CLASS_NAME, "thumbnail")

    for item in items:
        title = item.find_element(
            By.CLASS_NAME,
            "title"
        ).get_attribute("title").strip()
        description = item.find_element(
            By.CLASS_NAME,
            "description"
        ).text.strip()
        raw_price = item.find_element(By.CLASS_NAME, "price").text.strip()
        stars = item.find_elements(By.CLASS_NAME, "ws-icon-star")
        reviews = item.find_element(
            By.CSS_SELECTOR,
            "span[itemprop='reviewCount']"
        ).text.strip()

        results.append(
            Product(
                title=title,
                description=description,
                price=float(raw_price.replace("$", "")),
                rating=len(stars),
                num_of_reviews=int(reviews),
            )
        )
    return results


def process_pagination(driver: webdriver.Chrome) -> list[Product]:
    wait = WebDriverWait(driver, 5)
    while True:
        try:
            btn = wait.until(ec.element_to_be_clickable((
                By.CLASS_NAME,
                "btn-primary"
            )))
            driver.execute_script("arguments[0].click();", btn)
        except Exception:
            break
    return extract_page_data(driver)


def export_to_csv(name: str, data: list[Product]) -> None:
    header = [f.name for f in fields(Product)]
    with open(name, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        for pr in data:
            writer.writerow([
                pr.title,
                pr.description,
                pr.price,
                pr.rating,
                pr.num_of_reviews
            ])


def get_all_products() -> None:
    driver = get_driver()
    targets = {
        "home.csv": HOME_URL,
        "computers.csv": urljoin(HOME_URL, "computers"),
        "laptops.csv": urljoin(HOME_URL, "computers/laptops"),
        "tablets.csv": urljoin(HOME_URL, "computers/tablets"),
        "phones.csv": urljoin(HOME_URL, "phones"),
        "touch.csv": urljoin(HOME_URL, "phones/touch"),
    }

    try:
        for filee, url in targets.items():
            driver.get(url)
            clear_cookies(driver)
            products = process_pagination(driver)
            export_to_csv(filee, products)
    finally:
        driver.quit()


if __name__ == "__main__":
    get_all_products()
