import csv
import re
import time
from dataclasses import dataclass
from urllib.parse import urljoin
from tqdm import tqdm

from selenium import webdriver
from selenium.common.exceptions import (
    ElementClickInterceptedException,
    NoSuchElementException,
    StaleElementReferenceException,
    TimeoutException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait


BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


def _create_driver() -> webdriver.Chrome:
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    # Додаємо user-agent для кращої прохідності
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    driver = webdriver.Chrome(options=options)
    driver.set_page_load_timeout(30)
    return driver


def _scrape_page(driver: webdriver.Chrome, url: str, page_name: str) -> list[Product]:
    driver.get(url)
    _try_accept_cookies(driver)

    try:
        WebDriverWait(driver, 15).until(
            ec.presence_of_element_located((By.CSS_SELECTOR, "a.title"))
        )
    except TimeoutException:
        return []

    # Використовуємо tqdm для візуалізації кліків пагінації
    _click_load_more_until_end(driver, page_name)
    return _parse_products(driver)


def _try_accept_cookies(driver: webdriver.Chrome) -> None:
    fallback_xpath = "//button[contains(., 'Accept') or contains(., 'I agree')]"
    selectors = [
        (By.ID, "CybotCookiebotDialogBodyLevelButtonAccept"),
        (By.ID, "CybotCookiebotDialogBodyButtonAccept"),
        (By.ID, "onetrust-accept-btn-handler"),
        (By.CSS_SELECTOR, "button[aria-label='Accept']"),
        (By.XPATH, fallback_xpath),
    ]
    for by, selector in selectors:
        try:
            button = WebDriverWait(driver, 1).until(
                ec.element_to_be_clickable((by, selector))
            )
            button.click()
            return
        except:
            continue


def _click_load_more_until_end(driver: webdriver.Chrome, page_name: str) -> None:
    # Створюємо прогрес-бар для кожної сторінки
    pbar = tqdm(desc=f"Loading {page_name}", unit=" click", leave=False)
    while True:
        more_button = _find_more_button(driver)
        if more_button is None:
            break

        old_count = len(driver.find_elements(By.CSS_SELECTOR, "a.title"))
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", more_button)

        try:
            more_button.click()
        except:
            driver.execute_script("arguments[0].click();", more_button)

        try:
            # Чекаємо появи нових товарів
            WebDriverWait(driver, 10).until(
                lambda d: len(d.find_elements(By.CSS_SELECTOR, "a.title")) > old_count
            )
            pbar.update(1)
            time.sleep(0.2)
        except TimeoutException:
            break
    pbar.close()


def _find_more_button(driver: webdriver.Chrome) -> WebElement | None:
    selectors = [
        (By.CSS_SELECTOR, "a.ecomerce-items-scroll-more"),
        (By.CSS_SELECTOR, "button.ecomerce-items-scroll-more"),
        (By.CSS_SELECTOR, "#more"),
        (By.XPATH, "//a[contains(@class,'ecomerce-items-scroll-more') and not(contains(@class,'disabled'))]"),
    ]
    for by, selector in selectors:
        try:
            btn = driver.find_element(by, selector)
            if btn.is_displayed() and btn.is_enabled():
                return btn
        except NoSuchElementException:
            continue
    return None


def _parse_products(driver: webdriver.Chrome) -> list[Product]:
    product_cards = driver.find_elements(By.CSS_SELECTOR, "div.thumbnail")
    products: list[Product] = []

    # Можна додати tqdm і сюди, якщо товарів дуже багато
    for card in product_cards:
        try:
            title_el = card.find_element(By.CSS_SELECTOR, "a.title")
            title = title_el.get_attribute("title") or title_el.text
            description = card.find_element(By.CSS_SELECTOR, "p.description").text
            price = float(card.find_element(By.CSS_SELECTOR, "h4.price").text.replace("$", "").strip())

            rating = _parse_rating(card)
            reviews = _parse_reviews(card)

            products.append(Product(
                title=title.strip(),
                description=description.strip(),
                price=price,
                rating=rating,
                num_of_reviews=reviews
            ))
        except NoSuchElementException:
            continue
    return products


def _parse_rating(card: WebElement) -> int:
    # Бронебійний підхід до рейтингу
    stars = card.find_elements(By.CSS_SELECTOR, "div.ratings span.glyphicon-star")
    if not stars:
        stars = card.find_elements(By.CSS_SELECTOR, "div.ratings span.ws-icon-star")
    return len(stars)


def _parse_reviews(card: WebElement) -> int:
    try:
        text = card.find_element(By.CSS_SELECTOR, "div.ratings p.review-count, div.ratings p.pull-right").text
        match = re.search(r"\d+", text)
        return int(match.group(0)) if match else 0
    except NoSuchElementException:
        return 0


def _write_products(page_name: str, products: list[Product]) -> None:
    with open(f"{page_name}.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["title", "description", "price", "rating", "num_of_reviews"])
        for p in products:
            writer.writerow([p.title, p.description, p.price, p.rating, p.num_of_reviews])


def get_all_products() -> None:
    pages = {
        "home": HOME_URL,
        "computers": urljoin(HOME_URL, "computers"),
        "laptops": urljoin(HOME_URL, "computers/laptops"),
        "tablets": urljoin(HOME_URL, "computers/tablets"),
        "phones": urljoin(HOME_URL, "phones"),
        "touch": urljoin(HOME_URL, "phones/touch"),
    }

    driver = _create_driver()
    # Загальний прогрес по сторінках
    main_pbar = tqdm(pages.items(), desc="Overall Progress")
    try:
        for page_name, page_url in main_pbar:
            main_pbar.set_postfix(page=page_name)
            products = _scrape_page(driver, page_url, page_name)
            _write_products(page_name, products)
    finally:
        driver.quit()


if __name__ == "__main__":
    get_all_products()