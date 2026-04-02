import time
import csv
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.webdriver import WebDriver
from dataclasses import dataclass, fields, astuple
from urllib.parse import urljoin
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, NoSuchElementException


BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")


_driver: WebDriver | None = None


def get_driver() -> WebDriver:
    global _driver
    if _driver is None:
        options = Options()
        options.add_argument("--headless")  # no browser window
        _driver = webdriver.Chrome(options=options)
    return _driver


def set_driver(new_driver: WebDriver) -> None:
    global _driver
    _driver = new_driver


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int
    # additional_info: dict


PRODUCT_FIELDS = [field.name for field in fields(Product)]


def close_cookie_banner(current_driver: WebDriver) -> None:
    try:
        wait = WebDriverWait(current_driver, 5)
        cookie_btn = wait.until(EC.element_to_be_clickable((
            By.CSS_SELECTOR,
            "#cookieBanner button, #cookieBanner .btn, [id*='cookie'] button"
        )))
        cookie_btn.click()
        wait.until(EC.invisibility_of_element_located((By.ID, "cookieBanner")))
    except TimeoutException:
        pass


def get_one_product(card: BeautifulSoup) -> Product:
    title = card.select_one(".title")["title"]
    description = card.select_one(
        ".description").text.strip().replace("\xa0", " ")
    price = float(card.select_one(".price").text.strip().replace("$", ""))

    rating_el = card.select_one(".ratings p[data-rating]")
    if rating_el:
        rating = int(rating_el.get("data-rating"))
    else:
        rating = len(card.select(".ratings p .ws-icon-star"))

    num_of_reviews = int(card.select_one(".review-count span").text)

    return Product(
        title=title,
        description=description,
        price=price,
        rating=rating,
        num_of_reviews=num_of_reviews
    )


def get_subcategories_links(category_url: str) -> dict[str, str]:
    driver = get_driver()
    driver.get(category_url)
    close_cookie_banner(driver)
    subcategories_elements = driver.find_elements(
        By.CSS_SELECTOR,
        "#side-menu .nav-second-level .subcategory-link"
    )
    subcategories_links = {}
    for subcat in subcategories_elements:
        href = subcat.get_attribute("href")
        name = subcat.text.strip().lower()  # e.g. "laptops", "tablets"
        subcategories_links[name] = href
    return subcategories_links


def get_all_categories_links() -> dict[str, str]:
    driver = get_driver()
    driver.get(HOME_URL)
    close_cookie_banner(driver)
    categories = driver.find_elements(By.CSS_SELECTOR, "#side-menu > li > a")
    all_links = {}

    for cat in categories:
        href = cat.get_attribute("href")
        name = cat.text.strip().lower()
        all_links[name] = href

    for name, href in list(all_links.items()):
        sub_links = get_subcategories_links(href)
        all_links.update(sub_links)
    return all_links


def get_products_per_link(link: str) -> list[Product]:
    driver = get_driver()
    driver.get(link)
    close_cookie_banner(driver)

    while True:
        try:
            more_button = driver.find_element(
                By.CSS_SELECTOR, "a.ecomerce-items-scroll-more"
            )
            if not more_button.is_displayed():
                break
            driver.execute_script("arguments[0].click();", more_button)
            time.sleep(0.5)
        except NoSuchElementException:
            break

    page_soup = BeautifulSoup(driver.page_source, "html.parser")
    cards = page_soup.select("div.card.thumbnail")
    if cards:
        print(cards[0].prettify())
    return [get_one_product(card) for card in cards]


def get_all_products() -> None:
    links = get_all_categories_links()
    for name, href in links.items():
        write_products_info_to_csv(
            get_products_per_link(href), f"{name}.csv"
        )


def write_products_info_to_csv(
        products: list[Product],
        output_csv_path: str
) -> None:
    with open(output_csv_path, "w", encoding="utf-8", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(PRODUCT_FIELDS)
        writer.writerows([astuple(product) for product in products])


if __name__ == "__main__":
    with webdriver.Chrome() as driver:
        set_driver(driver)
        get_all_products()
